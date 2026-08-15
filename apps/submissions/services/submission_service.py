from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from apps.submissions.models import ExamAttempt, AttemptAnswer, ProctoringLog


@transaction.atomic
def finalize_submission(
    attempt: ExamAttempt,
    final_answers_delta: List[Dict[str, Any]] = None
) -> ExamAttempt:
    """
    Atomically finalizes an examination attempt:
    1. Saves any pending answers from the submit payload.
    2. Locks attempt status to SUBMITTED.
    3. Records submission timestamp and proctoring log.
    """
    if attempt.status != ExamAttempt.Status.IN_PROGRESS:
        return attempt

    # Save final delta if provided
    if final_answers_delta:
        from apps.submissions.services.heartbeat_service import process_heartbeat
        process_heartbeat(attempt, answers_delta=final_answers_delta)

    attempt.status = ExamAttempt.Status.SUBMITTED
    attempt.submitted_at = timezone.now()
    attempt.save(update_fields=['status', 'submitted_at'])

    ProctoringLog.objects.create(
        attempt=attempt,
        event_type=ProctoringLog.EventType.AUTO_SUBMISSION,
        details={'action': 'candidate_final_submit', 'is_simulation': attempt.is_simulation}
    )

    return attempt


def auto_submit_expired_attempts() -> int:
    """
    Scans and auto-submits all expired IN_PROGRESS attempts.
    Invoked by management command or background worker.
    """
    now = timezone.now()
    in_progress = ExamAttempt.objects.filter(status=ExamAttempt.Status.IN_PROGRESS)
    count = 0

    for attempt in in_progress:
        if attempt.is_expired:
            with transaction.atomic():
                attempt.status = ExamAttempt.Status.AUTO_SUBMITTED
                attempt.submitted_at = now
                attempt.save(update_fields=['status', 'submitted_at'])

                ProctoringLog.objects.create(
                    attempt=attempt,
                    event_type=ProctoringLog.EventType.AUTO_SUBMISSION,
                    details={'action': 'auto_submit_expired_timer'}
                )
                count += 1

    return count
