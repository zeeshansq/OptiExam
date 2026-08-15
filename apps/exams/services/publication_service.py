from django.db import transaction
from django.utils import timezone
from apps.exams.models import Exam, ExamParticipantRoster
from apps.accounts.models import Notification


@transaction.atomic
def publish_exam_results(
    exam: Exam,
    show_grader_feedback: bool,
    publisher_user
) -> Exam:
    """
    Publishes official results for an examination:
    1. Sets results_published = True and show_grader_feedback.
    2. Records published_at and published_by metadata.
    3. Dispatches in-app notification to all enrolled candidates.
    """
    exam.results_published = True
    exam.show_grader_feedback = show_grader_feedback
    exam.published_at = timezone.now()
    exam.published_by = publisher_user
    exam.save(update_fields=['results_published', 'show_grader_feedback', 'published_at', 'published_by'])

    # Dispatch notification to all enrolled participants
    roster_entries = ExamParticipantRoster.objects.filter(exam=exam).select_related('participant')
    for entry in roster_entries:
        Notification.objects.create(
            user=entry.participant,
            tenant=exam.tenant,
            notification_type=Notification.NotificationType.RESULT_PUBLISHED,
            title=f"Results Published: {exam.title}",
            message=f"Official scorecards for {exam.title} ({exam.code}) are now released and available for review.",
            link_url=f"/submissions/exams/{exam.id}/result/"
        )

    return exam
