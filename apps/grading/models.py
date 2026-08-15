from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TenantModelMixin
from apps.exams.models import Exam, ExamSection
from apps.submissions.models import ExamAttempt, AttemptAnswer


class GraderAllocation(TenantModelMixin):
    """
    Candidate batch partitioning matrix allocating candidate index ranges
    (e.g. Candidates 1–100 -> Grader A) with SLA deadlines.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed & Signed Off'

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='grader_allocations'
    )
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_grading_allocations'
    )
    section_scope = models.ForeignKey(
        ExamSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional section specialization (leave blank for all subjective sections)."
    )
    candidate_range_start = models.PositiveIntegerField(
        help_text="Starting sequential candidate index (e.g. 1)"
    )
    candidate_range_end = models.PositiveIntegerField(
        help_text="Ending sequential candidate index (e.g. 100)"
    )
    sla_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="SLA evaluation deadline for this batch."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['candidate_range_start']
        verbose_name = 'Grader Allocation'
        verbose_name_plural = 'Grader Allocations'

    def __str__(self):
        return f"{self.exam.code} — Candidates #{self.candidate_range_start:03d}–#{self.candidate_range_end:03d} -> {self.grader.username}"

    @property
    def total_candidates(self) -> int:
        return max(0, (self.candidate_range_end - self.candidate_range_start) + 1)

    @property
    def is_overdue(self) -> bool:
        if self.status == self.Status.COMPLETED or not self.sla_deadline:
            return False
        return timezone.now() > self.sla_deadline


class QuestionScore(models.Model):
    """
    Evaluated grade record for a subjective candidate response,
    supporting rubric-based criteria breakdowns and optimistic concurrency locking.
    """
    answer = models.OneToOneField(
        AttemptAnswer,
        on_delete=models.CASCADE,
        related_name='grade_record'
    )
    grader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_scores'
    )
    awarded_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0
    )
    rubric_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-criterion score map: {'rubric_id_1': 4.5, 'rubric_id_2': 3.0}"
    )
    examiner_notes = models.TextField(
        blank=True,
        help_text="Private internal moderation notes."
    )
    feedback_to_student = models.TextField(
        blank=True,
        help_text="Constructive remarks revealed to student only after results are published."
    )
    is_draft = models.BooleanField(
        default=True,
        help_text="True if evaluation is in-progress; False when finalized by grader."
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Optimistic concurrency control version lock."
    )
    graded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-graded_at']
        verbose_name = 'Question Score'
        verbose_name_plural = 'Question Scores'

    def __str__(self):
        return f"Score: {self.awarded_marks} pts on Answer #{self.answer.id} by {self.grader.username if self.grader else 'System'}"


class GradeModeration(models.Model):
    """
    Chief Examiner / Designer moderation audit and sign-off record.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Chief Review'
        APPROVED = 'APPROVED', 'Approved & Moderated'
        RETURNED = 'RETURNED', 'Returned for Revision'

    attempt = models.OneToOneField(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='grade_moderation'
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_attempts'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    moderation_notes = models.TextField(
        blank=True,
        help_text="Chief Examiner moderation feedback or revision directions."
    )
    total_final_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_passed = models.BooleanField(
        default=False
    )
    moderated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-moderated_at']
        verbose_name = 'Grade Moderation Record'
        verbose_name_plural = 'Grade Moderation Records'

    def __str__(self):
        return f"Moderation for Attempt #{self.attempt.id}: {self.get_status_display()}"
