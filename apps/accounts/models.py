from django.db import models
from django.contrib.auth.models import AbstractUser

class UserRole(models.TextChoices):
    SUPER_ADMIN  = 'SUPER_ADMIN',  'Super Admin (SaaS Manager)'
    DESIGNER     = 'DESIGNER',     'Designer (Tenant Admin)'
    ITEM_WRITER  = 'ITEM_WRITER',  'Item Writer (Subject Expert)'
    GRADER       = 'GRADER',       'Grader (Evaluation Officer)'
    PARTICIPANT  = 'PARTICIPANT',  'Participant (Student/Candidate)'

class User(AbstractUser):
    """
    Unified Custom User model for OptiExam's 5-tier role architecture.
    `tenant` is NULL only for platform-level Super Admins.
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text="Tenant institution association. Null only for SaaS Super Admins."
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PARTICIPANT,
        db_index=True
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='accounts/avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opti_users'
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['tenant', 'is_active']),
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

class UserProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='profile')
    registration_number = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    batch_year = models.CharField(max_length=20, blank=True, null=True)
    specialization = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'opti_user_profiles'

    def __str__(self):
        return f"Profile for {self.user.username} ({self.registration_number or 'No Reg #'})"

class AuditLog(models.Model):
    class ActionCategory(models.TextChoices):
        AUTH       = 'AUTH',       'Authentication Event'
        EXAM_OP    = 'EXAM_OP',    'Exam Operation'
        LIVE_OP    = 'LIVE_OP',    'Live Exam Operation'
        GRADING_OP = 'GRADING_OP', 'Grading Operation'
        ADMIN_OP   = 'ADMIN_OP',   'Admin Configuration'
        SECURITY   = 'SECURITY',   'Security & Access Control'

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

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.category} - {self.action} ({self.user})"
