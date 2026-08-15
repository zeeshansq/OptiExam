from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import GradeModeration, QuestionScore
from apps.accounts.models import User, Notification


@transaction.atomic
def approve_grade_moderation(
    moderation: GradeModeration,
    moderator: User,
    notes: str = ''
) -> GradeModeration:
    """
    Approves and locks evaluated candidate score.
    """
    moderation.moderator = moderator
    moderation.status = GradeModeration.Status.APPROVED
    moderation.moderation_notes = notes
    moderation.moderated_at = timezone.now()
    moderation.save(update_fields=['moderator', 'status', 'moderation_notes', 'moderated_at'])

    # Update attempt status to GRADED
    attempt = moderation.attempt
    attempt.status = ExamAttempt.Status.GRADED
    attempt.save(update_fields=['status'])

    return moderation


@transaction.atomic
def return_grade_for_reevaluation(
    moderation: GradeModeration,
    moderator: User,
    revision_notes: str
) -> GradeModeration:
    """
    Returns an evaluated attempt back to the examiner for re-evaluation.
    Unlocks question scores back to draft mode.
    """
    if not revision_notes.strip():
        raise ValidationError("Revision directions must be provided when returning for re-evaluation.")

    moderation.moderator = moderator
    moderation.status = GradeModeration.Status.RETURNED
    moderation.moderation_notes = revision_notes
    moderation.moderated_at = timezone.now()
    moderation.save(update_fields=['moderator', 'status', 'moderation_notes', 'moderated_at'])

    # Unlock subjective QuestionScores back to draft
    answers = AttemptAnswer.objects.filter(attempt=moderation.attempt)
    QuestionScore.objects.filter(answer__in=answers).update(is_draft=True)
    answers.update(is_graded=False)

    # Dispatch notification to Grader
    scores = QuestionScore.objects.filter(answer__in=answers, grader__isnull=False)
    graders = set(s.grader for s in scores)
    for g in graders:
        Notification.objects.create(
            user=g,
            tenant=moderation.attempt.tenant,
            notification_type=Notification.NotificationType.GRADING_ASSIGNED,
            title=f"Re-Evaluation Requested: Attempt #{moderation.attempt.id}",
            message=f"Chief Examiner requested revision on Attempt #{moderation.attempt.id}: {revision_notes}"
        )

    return moderation
