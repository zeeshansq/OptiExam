from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from apps.submissions.models import AttemptAnswer
from apps.grading.models import QuestionScore
from apps.grading.services.scoring_service import compute_attempt_totals


@transaction.atomic
def save_question_evaluation(
    answer: AttemptAnswer,
    grader,
    awarded_marks: Decimal,
    rubric_breakdown: Optional[Dict[str, float]] = None,
    examiner_notes: str = '',
    feedback_to_student: str = '',
    is_draft: bool = False,
    client_version: int = 1
) -> QuestionScore:
    """
    Evaluates a candidate's subjective response with optimistic concurrency locking and rubric scoring.
    """
    q = answer.question
    if awarded_marks > q.points:
        raise ValidationError(f"Awarded marks ({awarded_marks}) cannot exceed question max points ({q.points}).")

    score_obj, created = QuestionScore.objects.get_or_create(
        answer=answer,
        defaults={
            'grader': grader,
            'awarded_marks': awarded_marks,
            'rubric_breakdown': rubric_breakdown or {},
            'examiner_notes': examiner_notes,
            'feedback_to_student': feedback_to_student,
            'is_draft': is_draft,
            'version': 1
        }
    )

    if not created:
        # Optimistic concurrency check
        if client_version and score_obj.version != client_version:
            raise ValidationError("Concurrent edit detected: This evaluation was updated by another session. Please reload.")

        score_obj.grader = grader
        score_obj.awarded_marks = awarded_marks
        score_obj.rubric_breakdown = rubric_breakdown or {}
        score_obj.examiner_notes = examiner_notes
        score_obj.feedback_to_student = feedback_to_student
        score_obj.is_draft = is_draft
        score_obj.version += 1
        score_obj.save()

    # Update answer state
    answer.marks_awarded = awarded_marks
    answer.is_graded = not is_draft
    answer.save(update_fields=['marks_awarded', 'is_graded'])

    # Recompute attempt total
    compute_attempt_totals(answer.attempt)

    return score_obj
