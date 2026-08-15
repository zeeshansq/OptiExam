from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TenantModelMixin

class Exam(TenantModelMixin):
    """
    Core Exam Blueprint model containing scheduling, anti-cheat policy,
    lifeline configurations, and publication flags.
    """
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, help_text="Unique exam identifier (e.g. MID-2026-CS101)")
    subject = models.CharField(max_length=150, help_text="Discipline or Course Title")
    description = models.TextField(blank=True)
    instructions = models.TextField(
        blank=True,
        help_text="Detailed examination instructions and rules presented in the pre-exam lobby."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_exams'
    )
    start_time = models.DateTimeField(help_text="Start of the permitted schedule window.")
    end_time = models.DateTimeField(help_text="End of the permitted schedule window.")
    duration_minutes = models.PositiveIntegerField(default=60, help_text="Individual candidate examination duration limit.")
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100.0)
    passing_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.0)

    # Anti-Cheating & Security Policies
    enforce_fullscreen = models.BooleanField(default=True, help_text="Locks candidate into full-screen lockdown mode.")
    max_tab_switch_limit = models.PositiveIntegerField(default=3, help_text="Maximum allowed tab blur/switches before auto-submission.")
    lock_copy_paste = models.BooleanField(default=True, help_text="Disables clipboard copy/cut/paste events.")
    shuffle_questions = models.BooleanField(default=True, help_text="Randomizes question delivery order per student.")
    shuffle_options = models.BooleanField(default=True, help_text="Randomizes choice options per question.")
    allow_back_navigation = models.BooleanField(default=True, help_text="Allows candidates to navigate back to previous questions.")

    # Status & Life Cycle
    results_published = models.BooleanField(default=False, help_text="When True, candidates can inspect scores and feedback.")
    show_grader_feedback = models.BooleanField(default=True, help_text="Controls if examiner feedback notes are visible to student.")
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_exams'
    )
    is_active = models.BooleanField(default=True, help_text="Controls if this exam blueprint is active.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time', '-created_at']
        unique_together = ('tenant', 'code')
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    def __str__(self):
        return f"{self.title} ({self.code})"

    @property
    def total_assigned_questions(self) -> int:
        return sum(section.assignments.count() for section in self.sections.all())

    @property
    def total_enrolled_candidates(self) -> int:
        return self.roster_entries.count()


class ExamSection(models.Model):
    """
    Subdivisions within an examination (e.g. Section A: MCQs, Section B: Long Essay).
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    title = models.CharField(max_length=150, help_text="e.g. Section A - Objective MCQs")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    weightage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.0,
        help_text="Percentage weightage or marks allocated to this section."
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Exam Section'
        verbose_name_plural = 'Exam Sections'

    def __str__(self):
        return f"{self.exam.code} — {self.title}"


class ExamQuestionAssignment(models.Model):
    """
    M2M mapping between an ExamSection and a Question with custom display ordering
    and optional custom points override.
    """
    section = models.ForeignKey(
        ExamSection,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    question = models.ForeignKey(
        'questions.Question',
        on_delete=models.CASCADE,
        related_name='exam_assignments'
    )
    order = models.PositiveIntegerField(default=1)
    custom_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overrides base question points specifically for this exam."
    )

    class Meta:
        ordering = ['order', 'id']
        unique_together = ('section', 'question')
        verbose_name = 'Exam Question Assignment'
        verbose_name_plural = 'Exam Question Assignments'

    def __str__(self):
        return f"{self.section.title} -> Q#{self.question.id} (Order {self.order})"

    @property
    def effective_marks(self):
        return self.custom_marks if self.custom_marks is not None else self.question.points


class ExamLifelineConfig(models.Model):
    """
    Lifeline assistance rules configured for a specific exam.
    """
    class LifelineType(models.TextChoices):
        SKIP_QUESTION = 'SKIP_QUESTION', 'Skip Question'
        FIFTY_FIFTY = 'FIFTY_FIFTY', '50:50 Eliminator'
        HINT_TOKEN = 'HINT_TOKEN', 'Hint Token'
        BOOKMARK_FLAG = 'BOOKMARK_FLAG', 'Bookmark / Flag'

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='lifeline_configs'
    )
    lifeline_type = models.CharField(
        max_length=30,
        choices=LifelineType.choices
    )
    is_enabled = models.BooleanField(default=True)
    max_allowed = models.PositiveIntegerField(
        default=1,
        help_text="Maximum allowed uses per candidate during the exam."
    )

    class Meta:
        unique_together = ('exam', 'lifeline_type')
        verbose_name = 'Exam Lifeline Configuration'
        verbose_name_plural = 'Exam Lifeline Configurations'

    def __str__(self):
        return f"{self.exam.code} — {self.get_lifeline_type_display()} (Max: {self.max_allowed})"


class ExamParticipantRoster(models.Model):
    """
    Official roster of candidates authorized to sit for an exam, with sequential
    candidate_index used for double-blind human grading allocations.
    """
    class Status(models.TextChoices):
        ENROLLED = 'ENROLLED', 'Enrolled'
        ABSENT = 'ABSENT', 'Absent'
        REVOKED = 'REVOKED', 'Revoked / Barred'

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='roster_entries'
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrolled_exam_rosters'
    )
    candidate_index = models.PositiveIntegerField(
        db_index=True,
        help_text="Sequential integer 1..N assigned for double-blind grader allocation."
    )
    registration_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED
    )
    enrolled_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['candidate_index']
        unique_together = [('exam', 'participant'), ('exam', 'candidate_index')]
        verbose_name = 'Exam Participant Roster Entry'
        verbose_name_plural = 'Exam Participant Roster Entries'

    def __str__(self):
        return f"{self.exam.code} — Candidate #{self.candidate_index:03d} ({self.participant.username})"
