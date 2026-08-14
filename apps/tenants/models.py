from django.db import models

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

    def __str__(self):
        return f"{self.tenant.slug} - {self.get_feature_key_display()} ({'Enabled' if self.is_enabled else 'Disabled'})"
