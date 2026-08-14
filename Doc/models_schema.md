# Models Schema Specification — OptiExam Database Architecture
**Document Version:** 2.0.0  
**Target ORM:** Django 5.x ORM  
**Database Engines Supported:** SQLite (Dev/Offline) / PostgreSQL 16+ (Production SaaS)  
**Audited:** 2026-08-14 — Added missing models: `ExamParticipantRoster`, `ExamQuestionAssignment`, `ExamResult`, `GradeModeration`, `BroadcastAlert`. Added version locking to `QuestionScore`. Expanded indexes and constraints.

---

## Core Mixin (in `apps/core/models.py`)

```python
# apps/core/models.py
from django.db import models
from apps.core.managers import TenantManager

class TenantModelMixin(models.Model):
    """
    Abstract mixin that all tenant-scoped models MUST inherit.
    Enforces row-level tenant isolation across the entire ORM.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        db_index=True
    )
    objects = TenantManager()

    class Meta:
        abstract = True
```

---

## 1. App: `tenants`

### 1.1 `Tenant` Model
Represents an isolated educational institution, college, university, or corporate organization.

```python
class Tenant(models.Model):
    class Tier(models.TextChoices):
        STARTER      = 'STARTER',      'Starter (Single School / Lab, max 100 concurrent)'
        PROFESSIONAL = 'PROFESSIONAL',  'Professional (College / Multi-dept, max 500 concurrent)'
        ENTERPRISE   = 'ENTERPRISE',    'Enterprise (University / Multi-campus, unlimited)'

    name                     = models.CharField(max_length=200, help_text="Institutional display name")
    slug                     = models.SlugField(max_length=100, unique=True, db_index=True)
    domain                   = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text="Custom domain (optional)")
    tier                     = models.CharField(max_length=20, choices=Tier.choices, default=Tier.STARTER)
    is_active                = models.BooleanField(default=True, db_index=True)
    max_concurrent_candidates = models.PositiveIntegerField(default=100)
    logo                     = models.ImageField(upload_to='tenants/logos/', blank=True, null=True)
    primary_color            = models.CharField(max_length=7, default='#4F46E5', help_text="Hex color code for institutional branding")
    contact_email            = models.EmailField(blank=True, null=True)
    created_at               = models.DateTimeField(auto_now_add=True)
    updated_at               = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_tenants'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.slug})"
```

### 1.2 `TenantFeatureFlag` Model
Controls granular feature activations per tenant (managed by Super Admin).

```python
class TenantFeatureFlag(models.Model):
    class Feature(models.TextChoices):
        LIVE_PROCTORING      = 'LIVE_PROCTORING',      'Live Anti-Cheating & Proctoring'
        LIFELINES_ENGINE     = 'LIFELINES_ENGINE',     'Exam Lifelines System'
        DOUBLE_BLIND_GRADING = 'DOUBLE_BLIND_GRADING', 'Double-Blind Anonymized Evaluation'
        DYNAMIC_TIME_EXT     = 'DYNAMIC_TIME_EXT',     'Live Ops Time Extension'
        ADVANCED_ANALYTICS   = 'ADVANCED_ANALYTICS',   'Cohort Analytics & PDF Scorecards'
        GRADE_MODERATION     = 'GRADE_MODERATION',     'Chief Examiner Grade Moderation'
        CSV_ROSTER_IMPORT    = 'CSV_ROSTER_IMPORT',    'Bulk CSV Participant Roster Import'

    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='feature_flags')
    feature_key = models.CharField(max_length=50, choices=Feature.choices)
    is_enabled  = models.BooleanField(default=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_tenant_feature_flags'
        unique_together = ('tenant', 'feature_key')
```

---

## 2. App: `accounts`

### 2.1 `UserRole` TextChoices (module-level)
```python
class UserRole(models.TextChoices):
    SUPER_ADMIN  = 'SUPER_ADMIN',  'Super Admin (SaaS Manager)'
    DESIGNER     = 'DESIGNER',     'Designer (Tenant Admin)'
    ITEM_WRITER  = 'ITEM_WRITER',  'Item Writer (Subject Expert)'
    GRADER       = 'GRADER',       'Grader (Evaluation Officer)'
    PARTICIPANT  = 'PARTICIPANT',  'Participant (Student/Candidate)'
```

### 2.2 `User` Model (Custom `AbstractUser`)
```python
class User(AbstractUser):
    """
    Single custom user model for all 5 roles.
    tenant is NULL only for SUPER_ADMIN role.
    """
    tenant       = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE,
        null=True, blank=True, related_name='users',
        help_text="NULL only for SaaS Super Admins."
    )
    role         = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PARTICIPANT, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar       = models.ImageField(upload_to='accounts/avatars/', blank=True, null=True)
    is_verified  = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_users'
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    # Convenience properties
    def is_super_admin(self) -> bool:  return self.role == UserRole.SUPER_ADMIN or self.is_superuser
    def is_designer(self)   -> bool:   return self.role == UserRole.DESIGNER
    def is_item_writer(self)-> bool:   return self.role == UserRole.ITEM_WRITER
    def is_grader(self)     -> bool:   return self.role == UserRole.GRADER
    def is_participant(self)-> bool:   return self.role == UserRole.PARTICIPANT
```

### 2.3 `UserProfile` Model
```python
class UserProfile(models.Model):
    user                = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='profile')
    registration_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    department          = models.CharField(max_length=100, blank=True, null=True)
    batch_year          = models.CharField(max_length=20, blank=True, null=True)
    specialization      = models.CharField(max_length=150, blank=True, null=True)
    bio                 = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'opti_user_profiles'
```

### 2.4 `AuditLog` Model
```python
class AuditLog(models.Model):
    class ActionCategory(models.TextChoices):
        AUTH         = 'AUTH',         'Authentication Event'
        EXAM_OP      = 'EXAM_OP',      'Exam Operation'
        LIVE_OP      = 'LIVE_OP',      'Live Exam Operation'
        GRADING_OP   = 'GRADING_OP',   'Grading Operation'
        ADMIN_OP     = 'ADMIN_OP',     'Admin Configuration'
        SECURITY     = 'SECURITY',     'Security / Access Control'

    tenant     = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    user       = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    category   = models.CharField(max_length=20, choices=ActionCategory.choices, default=ActionCategory.ADMIN_OP, db_index=True)
    action     = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    payload    = models.JSONField(default=dict, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'opti_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
        ]
```

---

## 3. App: `exams`

### 3.1 `Exam` Model
```python
class Exam(TenantModelMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT       = 'DRAFT',       'Draft'
        PUBLISHED   = 'PUBLISHED',   'Published / Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'Active / Live'
        COMPLETED   = 'COMPLETED',   'Completed'
        ARCHIVED    = 'ARCHIVED',    'Archived'

    title              = models.CharField(max_length=255)
    code               = models.CharField(max_length=50, db_index=True)
    description        = models.TextField(blank=True)
    instructions       = models.TextField(help_text="Instructions displayed to candidates in the exam lobby")
    rules              = models.TextField(help_text="Exam conduct rules and anti-cheating policy text")
    created_by         = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='created_exams')
    status             = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)

    # Timing & Access Controls
    duration_minutes   = models.PositiveIntegerField(help_text="Total allowed duration in minutes")
    start_time         = models.DateTimeField(help_text="Exam window open time")
    end_time           = models.DateTimeField(help_text="Exam window close/lockdown time")
    is_force_enabled   = models.BooleanField(default=False, help_text="Override to enable exam regardless of schedule window")

    # Scoring & Pass Criteria
    total_marks        = models.DecimalField(max_digits=7, decimal_places=2, default=100.00)
    passing_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)

    # Anti-Cheating & Behavior Settings
    allow_back_navigation = models.BooleanField(default=True)
    shuffle_questions     = models.BooleanField(default=True)
    shuffle_options       = models.BooleanField(default=True)
    fullscreen_required   = models.BooleanField(default=True)
    max_tab_violations    = models.PositiveIntegerField(default=3)
    disable_copy_paste    = models.BooleanField(default=True)

    # Result Publication Control
    results_published     = models.BooleanField(default=False, db_index=True, help_text="Controls if participants can see results")
    show_grader_feedback  = models.BooleanField(default=True, help_text="If True, grader feedback is visible to participants after release")
    published_at          = models.DateTimeField(null=True, blank=True)
    published_by          = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='published_exams')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_exams'
        unique_together = ('tenant', 'code')
        ordering = ['-start_time']
```

### 3.2 `ExamSection` Model
```python
class ExamSection(models.Model):
    exam                 = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='sections')
    title                = models.CharField(max_length=150)
    order                = models.PositiveIntegerField(default=1)
    weightage_per_question = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    instructions         = models.TextField(blank=True)
    max_questions        = models.PositiveIntegerField(null=True, blank=True, help_text="Max questions drawn from pool (optional)")

    class Meta:
        db_table = 'opti_exam_sections'
        ordering = ['exam', 'order']
        unique_together = ('exam', 'order')
```

### 3.3 `ExamQuestionAssignment` Model *(NEW — Resolves GAP-10)*
Explicit M2M junction between Exam Sections and Questions, supporting ordering.

```python
class ExamQuestionAssignment(models.Model):
    """
    Explicitly tracks which questions are assigned to which exam sections.
    Enables Designer to reorder questions and set section-specific marks.
    """
    section      = models.ForeignKey('exams.ExamSection', on_delete=models.CASCADE, related_name='question_assignments')
    question     = models.ForeignKey('questions.Question', on_delete=models.PROTECT, related_name='exam_assignments')
    order        = models.PositiveIntegerField(default=1, help_text="Display order within the section")
    custom_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Override question marks for this exam only")
    added_by     = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='question_assignments')
    added_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_exam_question_assignments'
        unique_together = ('section', 'question')
        ordering = ['section', 'order']
```

### 3.4 `ExamParticipantRoster` Model *(NEW — Resolves GAP-01)*
Defines who is authorized to attempt a specific exam.

```python
class ExamParticipantRoster(models.Model):
    """
    Pre-enrollment roster. Only participants in this roster can start the exam.
    Populated via CSV import or manual add by Designer.
    """
    class Status(models.TextChoices):
        ENROLLED    = 'ENROLLED',    'Enrolled (Access Granted)'
        ABSENT      = 'ABSENT',      'Marked Absent'
        REVOKED     = 'REVOKED',     'Access Revoked'

    exam               = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='participant_roster')
    participant        = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='exam_enrollments')
    candidate_index    = models.PositiveIntegerField(db_index=True, help_text="Sequential roster number (1, 2, 3...) used for grader batch assignment")
    registration_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    status             = models.CharField(max_length=15, choices=Status.choices, default=Status.ENROLLED)
    added_by           = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='roster_additions')
    added_at           = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_exam_participant_roster'
        unique_together = ('exam', 'participant')
        ordering = ['exam', 'candidate_index']
        indexes = [
            models.Index(fields=['exam', 'candidate_index']),
            models.Index(fields=['exam', 'status']),
        ]
```

### 3.5 `ExamLifelineConfig` Model
```python
class LifelineType(models.TextChoices):
    SKIP_QUESTION = 'SKIP_QUESTION', 'Skip Question Quota'
    FIFTY_FIFTY   = 'FIFTY_FIFTY',   '50:50 Eliminator'
    HINT_TOKEN    = 'HINT_TOKEN',    'Hint Token'
    BOOKMARK_FLAG = 'BOOKMARK_FLAG', 'Review Bookmark'

class ExamLifelineConfig(models.Model):
    exam         = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='lifeline_configs')
    lifeline_type = models.CharField(max_length=30, choices=LifelineType.choices)
    is_enabled   = models.BooleanField(default=True)
    max_allowed  = models.PositiveIntegerField(default=2)

    class Meta:
        db_table = 'opti_exam_lifeline_configs'
        unique_together = ('exam', 'lifeline_type')
```

### 3.6 `ExamLiveEvent` Model
```python
class ExamLiveEvent(models.Model):
    class EventType(models.TextChoices):
        ADD_TIME          = 'ADD_TIME',          'Add Extra Time'
        BROADCAST_MESSAGE = 'BROADCAST_MESSAGE', 'Broadcast Live Announcement'
        FORCE_START       = 'FORCE_START',       'Force Start Attempt'
        FORCE_SUBMIT      = 'FORCE_SUBMIT',      'Force Submit Attempt'
        PUBLISH_RESULT    = 'PUBLISH_RESULT',    'Publish Exam Results'

    exam         = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='live_events')
    event_type   = models.CharField(max_length=30, choices=EventType.choices)
    target_type  = models.CharField(max_length=10, choices=[('ALL', 'All Candidates'), ('SINGLE', 'Single Candidate')], default='ALL')
    target_user  = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    data_payload = models.JSONField(default=dict)
    created_by   = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='dispatched_events')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_exam_live_events'
        ordering = ['-created_at']
```

---

## 4. App: `questions`

### 4.1 `QuestionBank` Model
```python
class QuestionBank(TenantModelMixin, models.Model):
    name       = models.CharField(max_length=200)
    code       = models.CharField(max_length=50)
    subject    = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_question_banks'
        unique_together = ('tenant', 'code')
```

### 4.2 `Question` Model
```python
class QuestionType(models.TextChoices):
    MCQ_SINGLE   = 'MCQ_SINGLE',   'Multiple Choice (Single Answer)'
    MCQ_MULTIPLE = 'MCQ_MULTIPLE', 'Multiple Choice (Multiple Answers)'
    IMAGE_MCQ    = 'IMAGE_MCQ',    'Picture / Diagram-based MCQ'
    SHORT_ANSWER = 'SHORT_ANSWER', 'Short Answer (Text / Word Limit)'
    LONG_ESSAY   = 'LONG_ESSAY',   'Long Essay / Structured Question'

class QuestionDifficulty(models.TextChoices):
    EASY   = 'EASY',   'Easy'
    MEDIUM = 'MEDIUM', 'Medium'
    HARD   = 'HARD',   'Hard'

class BloomsTaxonomyLevel(models.TextChoices):
    REMEMBER   = 'REMEMBER',   'Remember'
    UNDERSTAND = 'UNDERSTAND', 'Understand'
    APPLY      = 'APPLY',      'Apply'
    ANALYZE    = 'ANALYZE',    'Analyze'
    EVALUATE   = 'EVALUATE',   'Evaluate'
    CREATE     = 'CREATE',     'Create'

class Question(TenantModelMixin, models.Model):
    bank          = models.ForeignKey('questions.QuestionBank', on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=25, choices=QuestionType.choices, db_index=True)
    prompt        = models.TextField()
    image_asset   = models.ImageField(upload_to='questions/diagrams/', blank=True, null=True)
    points        = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    negative_points = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    word_limit    = models.PositiveIntegerField(null=True, blank=True, help_text="For SHORT_ANSWER questions only")
    difficulty    = models.CharField(max_length=10, choices=QuestionDifficulty.choices, default=QuestionDifficulty.MEDIUM)
    blooms_level  = models.CharField(max_length=15, choices=BloomsTaxonomyLevel.choices, blank=True, null=True)
    topic_tags    = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated topic tags")
    model_answer  = models.TextField(blank=True, null=True, help_text="Sample solution for Grader reference (not visible to candidates)")
    hint_text     = models.TextField(blank=True, null=True, help_text="Hint revealed if candidate uses Hint Token lifeline")
    explanation   = models.TextField(blank=True, null=True, help_text="Shown to candidates during post-exam review (if released)")
    is_active     = models.BooleanField(default=True, db_index=True)
    created_by    = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='authored_questions')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_questions'
        indexes = [
            models.Index(fields=['tenant', 'question_type']),
            models.Index(fields=['tenant', 'is_active']),
        ]
```

### 4.3 `QuestionOption` Model
```python
class QuestionOption(models.Model):
    question      = models.ForeignKey('questions.Question', on_delete=models.CASCADE, related_name='options')
    option_text   = models.CharField(max_length=500, blank=True)
    option_image  = models.ImageField(upload_to='questions/options/', blank=True, null=True)
    is_correct    = models.BooleanField(default=False)
    order         = models.PositiveIntegerField(default=1)
    explanation   = models.TextField(blank=True, help_text="Per-option explanation shown during post-exam review")

    class Meta:
        db_table = 'opti_question_options'
        ordering = ['order']
```

### 4.4 `QuestionRubric` Model
```python
class QuestionRubric(models.Model):
    question       = models.ForeignKey('questions.Question', on_delete=models.CASCADE, related_name='rubrics')
    criteria_title = models.CharField(max_length=150)
    description    = models.TextField(blank=True)
    max_points     = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    order          = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'opti_question_rubrics'
        ordering = ['order']
```

---

## 5. App: `submissions`

### 5.1 `ExamAttempt` Model
```python
class ExamAttempt(TenantModelMixin, models.Model):
    class Status(models.TextChoices):
        NOT_STARTED    = 'NOT_STARTED',    'Not Started'
        IN_PROGRESS    = 'IN_PROGRESS',    'In Progress'
        SUBMITTED      = 'SUBMITTED',      'Submitted by Candidate'
        AUTO_SUBMITTED = 'AUTO_SUBMITTED', 'Auto-Submitted (Timeout / Violation)'
        GRADED         = 'GRADED',         'Evaluation Finalized'

    exam                  = models.ForeignKey('exams.Exam', on_delete=models.PROTECT, related_name='attempts')
    participant           = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='exam_attempts')
    roster_entry          = models.ForeignKey('exams.ExamParticipantRoster', on_delete=models.PROTECT, null=True, blank=True, related_name='attempt')
    status                = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED, db_index=True)

    # Time Tracking (Server-Authoritative)
    started_at            = models.DateTimeField(null=True, blank=True)
    submitted_at          = models.DateTimeField(null=True, blank=True)
    bonus_minutes_awarded = models.PositiveIntegerField(default=0)
    last_heartbeat        = models.DateTimeField(null=True, blank=True, db_index=True)

    # State Resilience & Anti-Cheating
    resume_token          = models.CharField(max_length=64, unique=True, db_index=True)
    candidate_seed        = models.PositiveIntegerField(default=1, help_text="Deterministic seed for question/option shuffling")
    violation_count       = models.PositiveIntegerField(default=0)
    client_ip             = models.GenericIPAddressField(null=True, blank=True)
    user_agent            = models.CharField(max_length=255, blank=True, null=True)

    # Result Aggregates
    total_score           = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    is_passed             = models.BooleanField(default=False)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at            = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_exam_attempts'
        unique_together = ('exam', 'participant')
        indexes = [
            models.Index(fields=['exam', 'status']),
            models.Index(fields=['exam', 'last_heartbeat']),
        ]
```

### 5.2 `AttemptAnswer` Model
```python
class AttemptAnswer(models.Model):
    attempt             = models.ForeignKey('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='answers')
    question            = models.ForeignKey('questions.Question', on_delete=models.PROTECT, related_name='attempt_answers')
    selected_options    = models.ManyToManyField('questions.QuestionOption', blank=True)
    text_response       = models.TextField(blank=True, null=True)
    is_skipped          = models.BooleanField(default=False)
    is_bookmarked       = models.BooleanField(default=False)

    # Scoring State
    awarded_marks       = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_auto_graded      = models.BooleanField(default=False)
    is_verified_by_grader = models.BooleanField(default=False)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_attempt_answers'
        unique_together = ('attempt', 'question')
```

### 5.3 `ProctoringLog` Model
```python
class ProctoringLog(models.Model):
    class ViolationType(models.TextChoices):
        TAB_BLUR         = 'TAB_BLUR',         'Window Blur / Tab Switch'
        FULLSCREEN_EXIT  = 'FULLSCREEN_EXIT',  'Fullscreen Exit'
        KEYBOARD_LOCK    = 'KEYBOARD_LOCK',    'Restricted Key Shortcut'
        RIGHT_CLICK      = 'RIGHT_CLICK',      'Context Menu / Right-Click Attempt'
        DEVTOOLS_DETECT  = 'DEVTOOLS_DETECT',  'Developer Tools Opened'
        COPY_ATTEMPT     = 'COPY_ATTEMPT',     'Copy / Paste Attempt'
        AUTO_SUBMIT      = 'AUTO_SUBMIT',      'Max Violations: Auto-Submitted'

    class Severity(models.TextChoices):
        LOW      = 'LOW',      'Low Warning'
        MEDIUM   = 'MEDIUM',   'Medium Alert'
        CRITICAL = 'CRITICAL', 'Critical (Auto-Submit Trigger)'

    attempt        = models.ForeignKey('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='proctoring_logs')
    violation_type = models.CharField(max_length=30, choices=ViolationType.choices)
    severity       = models.CharField(max_length=15, choices=Severity.choices, default=Severity.LOW)
    details        = models.CharField(max_length=255, blank=True)
    timestamp      = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'opti_proctoring_logs'
        ordering = ['-timestamp']
```

### 5.4 `AttemptLifelineUsage` Model
```python
class AttemptLifelineUsage(models.Model):
    attempt       = models.ForeignKey('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='lifeline_usages')
    lifeline_type = models.CharField(max_length=30, choices=LifelineType.choices)
    question      = models.ForeignKey('questions.Question', on_delete=models.CASCADE)
    used_at       = models.DateTimeField(auto_now_add=True)
    details       = models.JSONField(default=dict, blank=True, help_text="e.g. eliminated option IDs for FIFTY_FIFTY")

    class Meta:
        db_table = 'opti_attempt_lifeline_usages'
```

---

## 6. App: `grading`

### 6.1 `GraderAllocation` Model
```python
class GraderAllocation(TenantModelMixin, models.Model):
    class Status(models.TextChoices):
        PENDING     = 'PENDING',     'Pending Evaluation'
        IN_PROGRESS = 'IN_PROGRESS', 'Evaluation In Progress'
        COMPLETED   = 'COMPLETED',   'Evaluation Completed'

    exam                  = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='grader_allocations')
    grader                = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='grading_assignments')
    candidate_range_start = models.PositiveIntegerField(help_text="Roster candidate_index start (e.g. 1)")
    candidate_range_end   = models.PositiveIntegerField(help_text="Roster candidate_index end (e.g. 100)")
    section_scope         = models.ForeignKey('exams.ExamSection', on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: scope to a specific section only")
    status                = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    deadline              = models.DateTimeField(help_text="SLA deadline for completing evaluation")
    assigned_at           = models.DateTimeField(auto_now_add=True)
    completed_at          = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'opti_grader_allocations'
        ordering = ['exam', 'candidate_range_start']
```

### 6.2 `QuestionScore` Model
```python
class QuestionScore(models.Model):
    """
    Individual question evaluation. Uses version field for optimistic concurrency locking
    to prevent race conditions when multiple graders might touch related records.
    """
    attempt_answer      = models.OneToOneField('submissions.AttemptAnswer', on_delete=models.CASCADE, related_name='score_record')
    grader              = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='evaluated_scores')
    allocation          = models.ForeignKey('grading.GraderAllocation', on_delete=models.SET_NULL, null=True, blank=True)
    marks_awarded       = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rubric_breakdown    = models.JSONField(default=dict, help_text="{'crit_1': 4.5, 'crit_2': 3.0}")
    grader_notes        = models.TextField(blank=True, help_text="Private notes for Chief Examiner")
    feedback_to_student = models.TextField(blank=True, help_text="Visible to candidate after result publication")
    is_draft            = models.BooleanField(default=True, db_index=True)
    version             = models.PositiveIntegerField(default=0, help_text="Optimistic locking version counter")
    evaluated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_question_scores'
```

### 6.3 `GradeModeration` Model *(NEW — Resolves GAP-03)*
Chief Examiner / Designer oversight and sign-off step before result publication.

```python
class GradeModeration(TenantModelMixin, models.Model):
    """
    Designer/Chief Examiner moderation record for an exam attempt.
    Created after all graders have finalized their evaluations.
    """
    class Status(models.TextChoices):
        PENDING    = 'PENDING',    'Awaiting Moderation Review'
        APPROVED   = 'APPROVED',   'Moderation Approved'
        RETURNED   = 'RETURNED',   'Returned for Re-Evaluation'

    exam         = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='moderations')
    attempt      = models.OneToOneField('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='moderation')
    moderator    = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='moderation_reviews')
    status       = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING, db_index=True)
    notes        = models.TextField(blank=True, help_text="Moderation notes or return reason")
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_grade_moderations'
```

---

## 7. App: `notifications`

### 7.1 `Notification` Model
```python
class Notification(TenantModelMixin, models.Model):
    class Type(models.TextChoices):
        SYSTEM           = 'SYSTEM',           'System Alert'
        EXAM_SCHEDULE    = 'EXAM_SCHEDULE',    'Exam Scheduled'
        TIME_EXTENSION   = 'TIME_EXTENSION',   'Bonus Time Awarded'
        GRADING_ASSIGNED = 'GRADING_ASSIGNED', 'New Grading Batch Assigned'
        GRADING_REMINDER = 'GRADING_REMINDER', 'Grading SLA Reminder'
        RESULT_PUBLISHED = 'RESULT_PUBLISHED', 'Exam Result Published'
        BROADCAST        = 'BROADCAST',        'Live Exam Broadcast'

    recipient         = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=25, choices=Type.choices, default=Type.SYSTEM)
    title             = models.CharField(max_length=200)
    message           = models.TextField()
    action_url        = models.CharField(max_length=255, blank=True, null=True)
    is_read           = models.BooleanField(default=False, db_index=True)
    priority          = models.PositiveSmallIntegerField(default=0, help_text="Higher = more urgent (0=normal, 1=high, 2=critical)")
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
```

### 7.2 `BroadcastAlert` Model *(NEW — for live exam cockpit alerts)*
```python
class BroadcastAlert(TenantModelMixin, models.Model):
    """
    Live broadcast alerts sent during active exams.
    Polled by the candidate cockpit heartbeat response.
    """
    exam       = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='broadcasts')
    message    = models.TextField()
    sent_by    = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    is_active  = models.BooleanField(default=True, db_index=True, help_text="False after broadcast window expires")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Auto-hide from cockpit after this time")

    class Meta:
        db_table = 'opti_broadcast_alerts'
        ordering = ['-created_at']
```

---

## 8. Relationship Summary Diagram

```
Tenant ──< User (role: DESIGNER, ITEM_WRITER, GRADER, PARTICIPANT)
Tenant ──< TenantFeatureFlag
Tenant ──< Exam ──< ExamSection ──< ExamQuestionAssignment >── Question
                  ──< ExamParticipantRoster >── User (PARTICIPANT)
                  ──< ExamLifelineConfig
                  ──< ExamLiveEvent
                  ──< GraderAllocation >── User (GRADER)
                  ──< BroadcastAlert
                  ──< ExamAttempt >── User (PARTICIPANT)
                                   ──< AttemptAnswer >── QuestionOption (M2M)
                                                      ──1 QuestionScore
                                   ──< ProctoringLog
                                   ──< AttemptLifelineUsage
                                   ──1 GradeModeration
Tenant ──< QuestionBank ──< Question ──< QuestionOption
                                     ──< QuestionRubric
Tenant ──< Notification >── User
```
