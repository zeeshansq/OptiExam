from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from apps.submissions.models import ExamAttempt, AttemptAnswer, ProctoringLog
from apps.questions.models import Question, QuestionOption


@transaction.atomic
def process_heartbeat(
    attempt: ExamAttempt,
    active_question_id: Optional[int] = None,
    answers_delta: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Processes the periodic 15-second client heartbeat:
    1. Updates attempt.last_heartbeat and current_question.
    2. Upserts incremental answers_delta to database.
    3. Checks if attempt has expired.
    4. Returns server-authoritative time sync and pending live broadcasts.
    """
    now = timezone.now()
    attempt.last_heartbeat = now

    # Check timeout expiry
    if attempt.is_expired:
        attempt.status = ExamAttempt.Status.AUTO_SUBMITTED
        attempt.submitted_at = now
        attempt.save(update_fields=['last_heartbeat', 'status', 'submitted_at'])
        return {
            'status': 'expired',
            'action': 'auto_submit',
            'message': 'Your examination time has expired. Your responses have been submitted.',
            'remaining_seconds': 0
        }

    # Update active question pointer if provided
    if active_question_id:
        if not attempt.current_question_id or attempt.current_question_id != active_question_id:
            attempt.current_question_id = active_question_id

    attempt.save(update_fields=['last_heartbeat', 'current_question'])

    # Save answers delta
    if answers_delta:
        for delta in answers_delta:
            q_id = delta.get('question_id')
            if not q_id:
                continue

            ans = AttemptAnswer.objects.filter(attempt=attempt, question_id=q_id).first()
            if not ans:
                continue

            # Update text response
            if 'text_response' in delta and delta['text_response'] is not None:
                ans.text_response = str(delta['text_response'])

            # Update bookmarks / skips
            if 'is_bookmarked' in delta:
                ans.is_bookmarked = bool(delta['is_bookmarked'])
            if 'is_skipped' in delta:
                ans.is_skipped = bool(delta['is_skipped'])

            ans.save()

            # Update selected options (MCQs)
            if 'selected_option_ids' in delta and isinstance(delta['selected_option_ids'], list):
                option_ids = delta['selected_option_ids']
                valid_options = QuestionOption.objects.filter(
                    question_id=q_id,
                    id__in=option_ids
                )
                ans.selected_options.set(valid_options)

    return {
        'status': 'active',
        'server_time': now.isoformat(),
        'remaining_seconds': attempt.remaining_seconds,
        'bonus_minutes_awarded': attempt.bonus_minutes_awarded,
        'violation_count': attempt.violation_count
    }
