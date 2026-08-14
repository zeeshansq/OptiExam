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

class DataImportJob(TenantModelMixin, models.Model):
    """
    Tracks the lifecycle of batch data imports (Rosters, Question Banks, Users, Rubrics).
    """
    class ImportType(models.TextChoices):
        PARTICIPANT_ROSTER = 'PARTICIPANT_ROSTER', 'Participant Exam Roster (CSV/Excel)'
        QUESTION_BANK      = 'QUESTION_BANK',      'Question Bank (CSV/Excel/JSON)'
        FACULTY_USERS      = 'FACULTY_USERS',      'Faculty / Graders / Item Writers (CSV/Excel)'
        RUBRIC_TEMPLATES   = 'RUBRIC_TEMPLATES',   'Grading Rubrics (CSV/JSON)'
        EXAM_BLUEPRINT     = 'EXAM_BLUEPRINT',     'Complete Exam Blueprint (JSON/YAML)'

    class Status(models.TextChoices):
        PENDING       = 'PENDING',       'Upload Received'
        VALIDATING    = 'VALIDATING',    'Dry-Run Validation In Progress'
        PREVIEW_READY = 'PREVIEW_READY', 'Validation Passed — Awaiting Confirmation'
        PROCESSING    = 'PROCESSING',    'Committing Records'
        COMPLETED     = 'COMPLETED',     'Import Successfully Completed'
        FAILED        = 'FAILED',        'Import Failed (Validation Errors)'

    class FileFormat(models.TextChoices):
        CSV   = 'CSV',   'CSV (.csv)'
        XLSX  = 'XLSX',  'Microsoft Excel (.xlsx)'
        JSON  = 'JSON',  'JSON (.json)'

    import_type     = models.CharField(max_length=30, choices=ImportType.choices, db_index=True)
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    file_format     = models.CharField(max_length=10, choices=FileFormat.choices, default=FileFormat.CSV)
    source_file     = models.FileField(upload_to='imports/raw/%Y/%m/')
    
    total_rows      = models.PositiveIntegerField(default=0)
    processed_rows  = models.PositiveIntegerField(default=0)
    successful_rows = models.PositiveIntegerField(default=0)
    failed_rows     = models.PositiveIntegerField(default=0)
    
    preview_data    = models.JSONField(default=list, blank=True)
    error_log       = models.JSONField(default=list, blank=True)
    
    created_by      = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='initiated_imports')
    created_at      = models.DateTimeField(auto_now_add=True)
    completed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'opti_data_import_jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'import_type', 'status']),
        ]

    def __str__(self):
        return f"{self.get_import_type_display()} - {self.get_status_display()} ({self.total_rows} rows)"
