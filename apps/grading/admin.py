from django.contrib import admin
from .models import GraderAllocation, QuestionScore, GradeModeration

@admin.register(GraderAllocation)
class GraderAllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'exam', 'grader', 'candidate_range_start', 'candidate_range_end', 'status', 'sla_deadline')
    list_filter = ('status', 'exam')
    search_fields = ('grader__username', 'exam__title')

@admin.register(QuestionScore)
class QuestionScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'answer', 'grader', 'awarded_marks', 'is_draft', 'version', 'graded_at')
    list_filter = ('is_draft',)

@admin.register(GradeModeration)
class GradeModerationAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'moderator', 'status', 'total_final_score', 'is_passed', 'moderated_at')
    list_filter = ('status', 'is_passed')
