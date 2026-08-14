from django.contrib import admin
from .models import QuestionBank, Question, QuestionOption, QuestionRubric

class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 2

class QuestionRubricInline(admin.TabularInline):
    model = QuestionRubric
    extra = 1

@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'subject', 'tenant', 'created_at')
    search_fields = ('name', 'code', 'subject')
    list_filter = ('tenant', 'subject')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('prompt_summary', 'question_type', 'bank', 'points', 'difficulty', 'blooms_level', 'tenant')
    list_filter = ('question_type', 'difficulty', 'blooms_level', 'tenant')
    search_fields = ('prompt', 'topic_tags')
    inlines = [QuestionOptionInline, QuestionRubricInline]

    def prompt_summary(self, obj):
        return obj.prompt[:60]
    prompt_summary.short_description = "Prompt"
