from django.db import models
from django.conf import settings
from apps.core.models import TenantModelMixin

class QuestionBank(TenantModelMixin):
    """
    Categorized repository of questions belonging to a specific institution.
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, help_text="e.g. CS101-BANK, MATH-ADV")
    subject = models.CharField(max_length=150, help_text="Academic discipline or course code")
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_question_banks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Question Bank'
        verbose_name_plural = 'Question Banks'

    def __str__(self):
        return f"{self.name} ({self.subject})"

    @property
    def question_count(self) -> int:
        return self.questions.count()


class Question(TenantModelMixin):
    """
    Core Question entity supporting 5 question formats, pedagogical tagging,
    diagram attachments, and scoring rubrics.
    """
    class QuestionType(models.TextChoices):
        MCQ_SINGLE = 'MCQ_SINGLE', 'Single Choice MCQ'
        MCQ_MULTIPLE = 'MCQ_MULTIPLE', 'Multiple Choice MCQ'
        IMAGE_MCQ = 'IMAGE_MCQ', 'Picture / Diagram MCQ'
        SHORT_ANSWER = 'SHORT_ANSWER', 'Short Answer'
        LONG_ESSAY = 'LONG_ESSAY', 'Long Essay / Structured'

    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Easy'
        MEDIUM = 'MEDIUM', 'Medium'
        HARD = 'HARD', 'Hard'

    class BloomsLevel(models.TextChoices):
        REMEMBER = 'REMEMBER', 'Remember'
        UNDERSTAND = 'UNDERSTAND', 'Understand'
        APPLY = 'APPLY', 'Apply'
        ANALYZE = 'ANALYZE', 'Analyze'
        EVALUATE = 'EVALUATE', 'Evaluate'
        CREATE = 'CREATE', 'Create'

    bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ_SINGLE,
        db_index=True
    )
    prompt = models.TextField(help_text="Primary question text or instructions.")
    image_asset = models.ImageField(
        upload_to='questions/diagrams/',
        null=True,
        blank=True,
        help_text="High-resolution diagram, chart, or visual asset for diagram-based questions."
    )
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=1.0,
        help_text="Base marks allocated to this question."
    )
    negative_points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text="Penalty points deducted for an incorrect response."
    )
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        db_index=True
    )
    blooms_level = models.CharField(
        max_length=15,
        choices=BloomsLevel.choices,
        default=BloomsLevel.REMEMBER,
        db_index=True
    )
    topic_tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated topic keywords (e.g. recursion, arrays, sorting)."
    )
    model_answer = models.TextField(
        blank=True,
        help_text="Confidential model answer and scoring guidelines for human evaluators."
    )
    hint_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Hint revealed if candidate consumes a Hint Token lifeline."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authored_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.prompt[:60]} ({self.points} pts)"

    @property
    def is_mcq(self) -> bool:
        return self.question_type in (
            self.QuestionType.MCQ_SINGLE,
            self.QuestionType.MCQ_MULTIPLE,
            self.QuestionType.IMAGE_MCQ
        )

    @property
    def is_subjective(self) -> bool:
        return self.question_type in (
            self.QuestionType.SHORT_ANSWER,
            self.QuestionType.LONG_ESSAY
        )


class QuestionOption(models.Model):
    """
    Choice options for Single, Multiple, and Diagram MCQs.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options'
    )
    option_text = models.CharField(max_length=500)
    option_image = models.ImageField(
        upload_to='questions/options/',
        null=True,
        blank=True,
        help_text="Optional diagram for this specific choice option."
    )
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(
        blank=True,
        help_text="Post-exam explanation of why this option is correct/incorrect."
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Question Option'
        verbose_name_plural = 'Question Options'

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.option_text[:50]}"


class QuestionRubric(models.Model):
    """
    Multi-criteria scoring rubric for Long Essay and Structured questions.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='rubrics'
    )
    criteria_title = models.CharField(max_length=200, help_text="e.g. Methodology, Code Correctness, Analysis")
    description = models.TextField(blank=True, help_text="Guidelines for awarding full vs partial points")
    max_points = models.DecimalField(max_digits=6, decimal_places=2)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Question Rubric Criteria'
        verbose_name_plural = 'Question Rubric Criteria'

    def __str__(self):
        return f"{self.criteria_title} ({self.max_points} pts)"
