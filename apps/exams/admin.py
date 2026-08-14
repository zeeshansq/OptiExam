from django.contrib import admin
from .models import Exam, ExamSection, ExamQuestionAssignment, ExamLifelineConfig, ExamParticipantRoster

class ExamSectionInline(admin.TabularInline):
    model = ExamSection
    extra = 1

class ExamLifelineConfigInline(admin.TabularInline):
    model = ExamLifelineConfig
    extra = 4

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'subject', 'start_time', 'end_time', 'duration_minutes', 'total_marks', 'is_active', 'tenant')
    list_filter = ('is_active', 'results_published', 'tenant')
    search_fields = ('title', 'code', 'subject')
    inlines = [ExamSectionInline, ExamLifelineConfigInline]

@admin.register(ExamParticipantRoster)
class ExamParticipantRosterAdmin(admin.ModelAdmin):
    list_display = ('exam', 'candidate_index', 'participant', 'registration_number', 'status', 'enrolled_at')
    list_filter = ('status', 'exam')
    search_fields = ('participant__username', 'participant__email', 'registration_number')
