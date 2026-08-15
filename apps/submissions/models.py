import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TenantModelMixin
from apps.exams.models import Exam, ExamSection, ExamLifelineConfig
from apps.questions.models import Question, QuestionOption


class ExamAttempt(TenantModelMixin):
    """
    Candidate examination attempt session.
    Tracks proctoring state, timers, seed, and completion status.
    """
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        AUTO_SUBMITTED = 'AUTO_SUBMITTED', 'Auto-Submitted (Expired / Violations)'
        DISQUALIFIED = 'DISQUALIFIED', 'Disqualified'

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_attempts'
    )
    resume_token = models.CharField(
        max_length=64,
        unique=True,
        default=uuid.uuid4,
        db_index=True,
        help_text="Cryptographic session resume token for crash recovery."
    )
    candidate_seed = models.BigIntegerField(
        help_text="Deterministic seed for reproducible randomized shuffling of questions and options."
    )
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    bonus_minutes_awarded = models.PositiveIntegerField(
        default=0,
        help_text="Dynamic time added on-the-fly by Designer in Live Ops."
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )
    last_heartbeat = models.DateTimeField(default=timezone.now)
    violation_count = models.PositiveIntegerField(default=0)
    current_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_in_attempts'
    )
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_simulation = models.BooleanField(
        default=False,
        help_text="True if run as a dry-run test sandbox by Designer / Item Writer. Excluded from official results."
    )

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Exam Attempt'
        verbose_name_plural = 'Exam Attempts'

    def __str__(self):
        sim_tag = " [SIMULATION]" if self.is_simulation else ""
        return f"{self.participant.username} — {self.exam.code} ({self.get_status_display()}){sim_tag}"

    @property
    def total_allowed_seconds(self):
        total_minutes = self.exam.duration_minutes + self.bonus_minutes_awarded
        return total_minutes * 60

    @property
    def remaining_seconds(self):
        if self.status != self.Status.IN_PROGRESS:
            return 0
        elapsed = (timezone.now() - self.started_at).total_seconds()
        remaining = self.total_allowed_seconds - elapsed
        return max(0, int(remaining))

    @property
    def is_expired(self):
        return self.remaining_seconds <= 0


class AttemptAnswer(models.Model):
    """
    Individual response submitted by a candidate for an assigned question.
    """
    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempt_answers'
    )
    selected_options = models.ManyToManyField(
        QuestionOption,
        blank=True,
        related_name='selected_in_answers'
    )
    text_response = models.TextField(blank=True, default='')
    is_bookmarked = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    order_in_attempt = models.PositiveIntegerField(default=1)
    saved_at = models.DateTimeField(auto_now=True)

    # Automated / Manual grading placeholders (scored in Phase 4)
    marks_awarded = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_graded = models.BooleanField(default=False)

    class Meta:
        ordering = ['order_in_attempt']
        unique_together = ('attempt', 'question')
        verbose_name = 'Attempt Answer'
        verbose_name_plural = 'Attempt Answers'

    def __str__(self):
        return f"Attempt #{self.attempt.id} -> Q#{self.question.id} (Order {self.order_in_attempt})"


class ProctoringLog(models.Model):
    """
    Real-time anti-cheating telemetry and proctoring violation stream.
    """
    class EventType(models.TextChoices):
        FULLSCREEN_ENTER = 'FULLSCREEN_ENTER', 'Entered Fullscreen'
        FULLSCREEN_EXIT = 'FULLSCREEN_EXIT', 'Exited Fullscreen Lockdown'
        TAB_BLUR = 'TAB_BLUR', 'Window Lost Focus / Tab Switched'
        CLIPBOARD_BLOCKED = 'CLIPBOARD_BLOCKED', 'Copy / Paste Attempt Intercepted'
        DEVTOOLS_BLOCKED = 'DEVTOOLS_BLOCKED', 'Developer Tools / Inspect Key Intercepted'
        HEARTBEAT_DISCONNECTED = 'HEARTBEAT_DISCONNECTED', 'Heartbeat Signal Disconnected'
        HEARTBEAT_RECONNECTED = 'HEARTBEAT_RECONNECTED', 'Heartbeat Signal Reconnected'
        LIFELINE_USED = 'LIFELINE_USED', 'Lifeline Executed'
        AUTO_SUBMISSION = 'AUTO_SUBMISSION', 'Auto-Submission Triggered'

    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='proctoring_logs'
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Proctoring Log'
        verbose_name_plural = 'Proctoring Logs'

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] Attempt #{self.attempt.id}: {self.get_event_type_display()}"


class AttemptLifelineUsage(models.Model):
    """
    Lifeline assistance records utilized by a candidate during an attempt.
    """
    attempt = models.ForeignKey(
        ExamAttempt,
        on_delete=models.CASCADE,
        related_name='lifeline_usages'
    )
    lifeline_type = models.CharField(
        max_length=30,
        choices=ExamLifelineConfig.LifelineType.choices
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='lifeline_usages'
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="e.g. {'eliminated_option_ids': [12, 15]} for 50:50, or {'hint_shown': true}"
    )
    used_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-used_at']
        verbose_name = 'Attempt Lifeline Usage'
        verbose_name_plural = 'Attempt Lifeline Usages'

    def __str__(self):
        return f"Attempt #{self.attempt.id} — {self.get_lifeline_type_display()} on Q#{self.question.id}"
