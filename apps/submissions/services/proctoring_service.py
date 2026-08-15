from typing import Dict, Any
from django.utils import timezone
from django.db import transaction
from apps.submissions.models import ExamAttempt, ProctoringLog


def log_proctoring_event(
    attempt: ExamAttempt,
    event_type: str,
    details: Dict[str, Any] = None
) -> ProctoringLog:
    """
    Safely logs anti-cheating events into the proctoring stream without interrupting session.
    """
    try:
        log = ProctoringLog.objects.create(
            attempt=attempt,
            event_type=event_type,
            details=details or {}
        )

        # Increment violation counter on actionable violations
        if event_type in (ProctoringLog.EventType.TAB_BLUR, ProctoringLog.EventType.FULLSCREEN_EXIT):
            attempt.violation_count += 1
            attempt.save(update_fields=['violation_count'])

            # Check violation escalation limit
            max_limit = attempt.exam.max_tab_switch_limit
            if max_limit and attempt.violation_count >= max_limit:
                attempt.status = ExamAttempt.Status.AUTO_SUBMITTED
                attempt.submitted_at = timezone.now()
                attempt.save(update_fields=['status', 'submitted_at'])
                
                ProctoringLog.objects.create(
                    attempt=attempt,
                    event_type=ProctoringLog.EventType.AUTO_SUBMISSION,
                    details={'reason': f'Exceeded maximum permitted violations ({max_limit}).'}
                )

        return log
    except Exception as e:
        # Non-blocking proctoring rule
        return None
