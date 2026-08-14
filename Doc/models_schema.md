# Models Schema Specification — OptiExam Database Architecture
**Document Version:** 1.0.0  
**Target ORM:** Django 5.x ORM  
**Database Engines Supported:** SQLite (Dev/Offline) / PostgreSQL 16+ (Production SaaS)  
**Document Scope:** Detailed model schemas, field types, default values, validators, constraints, choices, and indexes across all Django apps.

---

## 1. App: `tenants`

### 1.1 `Tenant` Model
Represents an isolated educational institution, college, university, or corporate organization.

```python
class Tenant(models.Model):
    class Tier(models.TextChoices):
        STARTER = 'STARTER', 'Starter (Single School / Lab)'
        PROFESSIONAL = 'PROFESSIONAL', 'Professional (College / Multi-department)'
        ENTERPRISE = 'ENTERPRISE', 'Enterprise (University / Multi-campus)'

    name = models.CharField(max_length=200, help_text="Institutional display name")
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    domain = models.CharField(max_length=255, blank=True, null=True, unique=True, help_text="Custom domain if applicable")
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.STARTER)
    is_active = models.BooleanField(default=True)
    max_concurrent_candidates = models.PositiveIntegerField(default=100)
    logo = models.ImageField(upload_to='tenants/logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#4F46E5', help_text="Hex color code for institutional branding")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_tenants'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.slug})"
```

### 1.2 `TenantFeatureFlag` Model
Controls granular feature activations per tenant.

```python
class TenantFeatureFlag(models.Model):
    class Feature(models.TextChoices):
        LIVE_PROCTORING = 'LIVE_PROCTORING', 'Live Anti-Cheating & Proctoring'
        LIFELINES_ENGINE = 'LIFELINES_ENGINE', 'Exam Lifelines System'
        DOUBLE_BLIND_GRADING = 'DOUBLE_BLIND_GRADING', 'Double-Blind Anonymized Evaluation'
        DYNAMIC_TIME_EXTENSION = 'DYNAMIC_TIME_EXTENSION', 'Live Ops Time Extension'
        ADVANCED_ANALYTICS = 'ADVANCED_ANALYTICS', 'Cohort Analytics & PDF Scorecards'

    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='feature_flags')
    feature_key = models.CharField(max_length=50, choices=Feature.choices)
    is_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_tenant_feature_flags'
        unique_together = ('tenant', 'feature_key')
```

---

## 2. App: `accounts`

### 2.1 `User` Model (Custom `AbstractUser`)
Implements the 5-tier user architecture.

```python
from django.contrib.auth.models import AbstractUser

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin (SaaS Manager)'
    DESIGNER = 'DESIGNER', 'Designer (Tenant Admin)'
    ITEM_WRITER = 'ITEM_WRITER', 'Item Writer (Subject Expert)'
    GRADER = 'GRADER', 'Grader (Evaluation Officer)'
    PARTICIPANT = 'PARTICIPANT', 'Participant (Student/Candidate)'

class User(AbstractUser):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text="Tenant association. Null only for SaaS Super Admins."
    )
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PARTICIPANT, db_index=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='accounts/avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_users'
        indexes = [
            models.Index(fields=['tenant', 'role']),
        ]

    def is_super_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN or self.is_superuser

    def is_designer(self) -> bool:
        return self.role == UserRole.DESIGNER

    def is_item_writer(self) -> bool:
        return self.role == UserRole.ITEM_WRITER

    def is_grader(self) -> bool:
        return self.role == UserRole.GRADER

    def is_participant(self) -> bool:
        return self.role == UserRole.PARTICIPANT
```

### 2.2 `UserProfile` Model
Stores extended metadata for examinees and faculty members.

```python
class UserProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='profile')
    registration_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    batch_year = models.CharField(max_length=20, blank=True, null=True)
    specialization = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'opti_user_profiles'
```

### 2.3 `AuditLog` Model
Tracks security events, logins, time grants, and configuration updates.

```python
class AuditLog(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'opti_audit_logs'
        ordering = ['-timestamp']
```

---

## 3. App: `exams`

### 3.1 `Exam` Model
Core blueprint of an examination.

```python
class Exam(TenantModelMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published / Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'Active / Live'
        COMPLETED = 'COMPLETED', 'Completed'
        ARCHIVED = 'ARCHIVED', 'Archived'

    title = models.CharField(max_length=255)
    code = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True)
    instructions = models.TextField(help_text="Instructions displayed to candidates in the lobby before attempt")
    rules = models.TextField(help_text="Anti-cheating rules and exam constraints")
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='created_exams')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    
    # Timing & Access Controls
    duration_minutes = models.PositiveIntegerField(help_text="Total allowed duration in minutes")
    start_time = models.DateTimeField(help_text="Exam window open time")
    end_time = models.DateTimeField(help_text="Exam window close time")
    is_force_enabled = models.BooleanField(default=False, help_text="Designer override to force enable exam regardless of time window")
    
    # Scoring & Pass Criteria
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100.00)
    passing_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=40.00)
    
    # Anti-Cheating & Behavior Settings
    allow_back_navigation = models.BooleanField(default=True, help_text="Allow moving backward to previous questions")
    shuffle_questions = models.BooleanField(default=True, help_text="Randomize question order per candidate")
    shuffle_options = models.BooleanField(default=True, help_text="Randomize MCQ options per candidate")
    fullscreen_required = models.BooleanField(default=True, help_text="Lock examination cockpit to fullscreen")
    max_tab_violations = models.PositiveIntegerField(default=3, help_text="Max allowed tab switch / blur events before auto-submission")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_exams'
        unique_together = ('tenant', 'code')
        ordering = ['-start_time']
```

### 3.2 `ExamSection` Model
Partitions an exam into distinct sections (e.g., Section A: Physics MCQs, Section B: Physics Essay).

```python
class ExamSection(models.Model):
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=1)
    weightage_per_question = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    instructions = models.TextField(blank=True)

    class Meta:
        db_table = 'opti_exam_sections'
        ordering = ['order']
```

### 3.3 `ExamLifelineConfig` Model
Configures lifelines available for a specific exam.

```python
class LifelineType(models.TextChoices):
    SKIP_QUESTION = 'SKIP_QUESTION', 'Skip Question Quota'
    FIFTY_FIFTY = 'FIFTY_FIFTY', '50:50 Eliminator'
    HINT_TOKEN = 'HINT_TOKEN', 'Hint Token'
    BOOKMARK_FLAG = 'BOOKMARK_FLAG', 'Review Bookmark'

class ExamLifelineConfig(models.Model):
    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='lifeline_configs')
    lifeline_type = models.CharField(max_length=30, choices=LifelineType.choices)
    is_enabled = models.BooleanField(default=True)
    max_allowed = models.PositiveIntegerField(default=2, help_text="Maximum number of times this lifeline can be used in this exam")

    class Meta:
        db_table = 'opti_exam_lifeline_configs'
        unique_together = ('exam', 'lifeline_type')
```

### 3.4 `ExamLiveEvent` Model
Logs live control room actions executed by the Designer.

```python
class ExamLiveEvent(models.Model):
    class EventType(models.TextChoices):
        ADD_TIME = 'ADD_TIME', 'Add Extra Time'
        BROADCAST_MESSAGE = 'BROADCAST_MESSAGE', 'Broadcast Live Announcement'
        FORCE_START = 'FORCE_START', 'Force Start Attempt'
        FORCE_SUBMIT = 'FORCE_SUBMIT', 'Force Submit Attempt'

    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='live_events')
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    target_type = models.CharField(max_length=20, choices=[('ALL', 'All Candidates'), ('SINGLE', 'Single Candidate')], default='ALL')
    target_user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    data_payload = models.JSONField(default=dict, help_text="Event specifics, e.g. {'minutes': 10, 'message': '...'}")
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='dispatched_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_exam_live_events'
        ordering = ['-created_at']
```

---

## 4. App: `questions`

### 4.1 `QuestionBank` Model
Curated repository of questions organized by subject.

```python
class QuestionBank(TenantModelMixin, models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    subject = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_question_banks'
        unique_together = ('tenant', 'code')
```

### 4.2 `Question` Model
Core question model supporting all 5 question types.

```python
class QuestionType(models.TextChoices):
    MCQ_SINGLE = 'MCQ_SINGLE', 'Multiple Choice (Single Answer)'
    MCQ_MULTIPLE = 'MCQ_MULTIPLE', 'Multiple Choice (Multiple Answers)'
    IMAGE_MCQ = 'IMAGE_MCQ', 'Picture / Diagram-based MCQ'
    SHORT_ANSWER = 'SHORT_ANSWER', 'Short Answer (Text/Word Limit)'
    LONG_ESSAY = 'LONG_ESSAY', 'Long Essay / Structured Question'

class QuestionDifficulty(models.TextChoices):
    EASY = 'EASY', 'Easy'
    MEDIUM = 'MEDIUM', 'Medium'
    HARD = 'HARD', 'Hard'

class Question(TenantModelMixin, models.Model):
    bank = models.ForeignKey('questions.QuestionBank', on_delete=models.CASCADE, related_name='questions')
    section = models.ForeignKey('exams.ExamSection', on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    question_type = models.CharField(max_length=25, choices=QuestionType.choices, db_index=True)
    prompt = models.TextField(help_text="The question prompt or problem statement")
    image_asset = models.ImageField(upload_to='questions/diagrams/', blank=True, null=True, help_text="Locally stored diagram/picture")
    points = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    negative_points = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    difficulty = models.CharField(max_length=10, choices=QuestionDifficulty.choices, default=QuestionDifficulty.MEDIUM)
    model_answer = models.TextField(blank=True, null=True, help_text="Sample solution for Grader reference")
    hint_text = models.TextField(blank=True, null=True, help_text="Hint revealed if candidate uses Hint Token")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='authored_questions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_questions'
```

### 4.3 `QuestionOption` Model
Stores individual options for MCQ questions.

```python
class QuestionOption(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500, blank=True)
    option_image = models.ImageField(upload_to='questions/options/', blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text="Explanation shown during post-exam review")

    class Meta:
        db_table = 'opti_question_options'
        ordering = ['order']
```

### 4.4 `QuestionRubric` Model
Scoring criteria for Short and Long Essay questions.

```python
class QuestionRubric(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, related_name='rubrics')
    criteria_title = models.CharField(max_length=150, help_text="e.g. 'Conceptual Clarity', 'Step-by-step Working'")
    description = models.TextField(blank=True)
    max_points = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'opti_question_rubrics'
        ordering = ['order']
```

---

## 5. App: `submissions`

### 5.1 `ExamAttempt` Model
Represents a candidate's live examination session.

```python
class ExamAttempt(TenantModelMixin, models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted by Candidate'
        AUTO_SUBMITTED = 'AUTO_SUBMITTED', 'Auto-Submitted (Timeout / Violation)'
        GRADED = 'GRADED', 'Evaluation Finalized'

    exam = models.ForeignKey('exams.Exam', on_delete=models.PROTECT, related_name='attempts')
    participant = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='exam_attempts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED, db_index=True)
    
    # Time Tracking (Server-Authoritative)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    bonus_minutes_awarded = models.PositiveIntegerField(default=0)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    
    # State Resilience & Security
    resume_token = models.CharField(max_length=64, unique=True, db_index=True)
    candidate_seed = models.PositiveIntegerField(default=1, help_text="Deterministic seed for question/option shuffling")
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    
    # Result Aggregates
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    is_passed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_exam_attempts'
        unique_together = ('exam', 'participant')
```

### 5.2 `AttemptAnswer` Model
Stores a candidate's answer to a specific question.

```python
class AttemptAnswer(models.Model):
    attempt = models.ForeignKey('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('questions.Question', on_delete=models.PROTECT, related_name='attempt_answers')
    selected_options = models.ManyToManyField('questions.QuestionOption', blank=True)
    text_response = models.TextField(blank=True, null=True)
    is_skipped = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)
    
    # Scoring State
    awarded_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_auto_graded = models.BooleanField(default=False)
    is_verified_by_grader = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_attempt_answers'
        unique_together = ('attempt', 'question')
```

### 5.3 `ProctoringLog` Model
Captures real-time integrity and anti-cheating incidents.

```python
class ProctoringLog(models.Model):
    class ViolationType(models.TextChoices):
        TAB_BLUR = 'TAB_BLUR', 'Window Blur / Tab Switch'
        FULLSCREEN_EXIT = 'FULLSCREEN_EXIT', 'Fullscreen Exit'
        KEYBOARD_LOCK = 'KEYBOARD_LOCK', 'Restricted Key Shortcut Pressed'
        RIGHT_CLICK = 'RIGHT_CLICK', 'Context Menu / Copy Attempt'
        DEVTOOLS_DETECTED = 'DEVTOOLS_DETECTED', 'Developer Tools Opened'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low Warning'
        MEDIUM = 'MEDIUM', 'Medium Alert'
        CRITICAL = 'CRITICAL', 'Critical Violation'

    attempt = models.ForeignKey('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='proctoring_logs')
    violation_type = models.CharField(max_length=30, choices=ViolationType.choices)
    severity = models.CharField(max_length=15, choices=Severity.choices, default=Severity.LOW)
    details = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'opti_proctoring_logs'
        ordering = ['-timestamp']
```

### 5.4 `AttemptLifelineUsage` Model
Tracks candidate lifeline consumption.

```python
class AttemptLifelineUsage(models.Model):
    attempt = models.ForeignKey('submissions.ExamAttempt', on_delete=models.CASCADE, related_name='lifeline_usages')
    lifeline_type = models.CharField(max_length=30, choices=LifelineType.choices)
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'opti_attempt_lifeline_usages'
```

---

## 6. App: `grading`

### 6.1 `GraderAllocation` Model
Implements the distributed candidate batch partitioning matrix.

```python
class GraderAllocation(TenantModelMixin, models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Evaluation'
        IN_PROGRESS = 'IN_PROGRESS', 'Evaluation In Progress'
        COMPLETED = 'COMPLETED', 'Evaluation Completed'

    exam = models.ForeignKey('exams.Exam', on_delete=models.CASCADE, related_name='grader_allocations')
    grader = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='grading_assignments')
    candidate_range_start = models.PositiveIntegerField(help_text="Starting index of candidate batch, e.g. 1")
    candidate_range_end = models.PositiveIntegerField(help_text="Ending index of candidate batch, e.g. 100")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    deadline = models.DateTimeField(help_text="SLA deadline for marking completion")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_grader_allocations'
        ordering = ['exam', 'candidate_range_start']
```

### 6.2 `QuestionScore` Model
Stores individual question evaluation marks, rubric selections, and examiner notes.

```python
class QuestionScore(models.Model):
    attempt_answer = models.OneToOneField('submissions.AttemptAnswer', on_delete=models.CASCADE, related_name='score_record')
    grader = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='evaluated_scores')
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    rubric_breakdown = models.JSONField(default=dict, help_text="Scored points per rubric criterion")
    grader_notes = models.TextField(blank=True, help_text="Private notes for internal moderation")
    feedback_to_student = models.TextField(blank=True, help_text="Constructive feedback visible to candidate")
    is_draft = models.BooleanField(default=True, help_text="True if evaluation is in progress; False if finalized")
    evaluated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_question_scores'
```

---

## 7. App: `notifications`

### 7.1 `Notification` Model
Powers the in-app top-nav notification bell.

```python
class Notification(TenantModelMixin, models.Model):
    class Type(models.TextChoices):
        SYSTEM = 'SYSTEM', 'System Alert'
        EXAM_SCHEDULE = 'EXAM_SCHEDULE', 'Exam Schedule Notification'
        TIME_EXTENSION = 'TIME_EXTENSION', 'Bonus Time Awarded'
        GRADING_ASSIGNED = 'GRADING_ASSIGNED', 'New Grading Batch Assigned'
        RESULT_PUBLISHED = 'RESULT_PUBLISHED', 'Exam Result Published'

    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'opti_notifications'
        ordering = ['-created_at']
```
