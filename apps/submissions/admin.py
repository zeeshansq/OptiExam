from django.contrib import admin
from .models import ExamAttempt, AttemptAnswer, ProctoringLog, AttemptLifelineUsage

@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant', 'exam', 'status', 'is_simulation', 'remaining_seconds', 'violation_count', 'started_at')
    list_filter = ('status', 'is_simulation', 'exam')
    search_fields = ('participant__username', 'participant__email', 'resume_token')

@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'order_in_attempt', 'is_bookmarked', 'is_skipped', 'saved_at')
    list_filter = ('is_bookmarked', 'is_skipped')

@admin.register(ProctoringLog)
class ProctoringLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'event_type', 'timestamp')
    list_filter = ('event_type',)

@admin.register(AttemptLifelineUsage)
class AttemptLifelineUsageAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'lifeline_type', 'question', 'used_at')
