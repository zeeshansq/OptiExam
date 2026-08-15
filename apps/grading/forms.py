from django import forms
from apps.grading.models import GraderAllocation, QuestionScore, GradeModeration
from apps.accounts.models import User, UserRole
from apps.exams.models import ExamSection


class GraderAllocationForm(forms.ModelForm):
    class Meta:
        model = GraderAllocation
        fields = ['grader', 'section_scope', 'candidate_range_start', 'candidate_range_end', 'sla_deadline']
        widgets = {
            'grader': forms.Select(attrs={'class': 'form-select'}),
            'section_scope': forms.Select(attrs={'class': 'form-select'}),
            'candidate_range_start': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'candidate_range_end': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
            'sla_deadline': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, exam=None, **kwargs):
        super().__init__(*args, **kwargs)
        if exam:
            self.fields['grader'].queryset = User.objects.filter(
                tenant=exam.tenant,
                role__in=[UserRole.GRADER, UserRole.DESIGNER]
            )
            self.fields['section_scope'].queryset = ExamSection.objects.filter(exam=exam)


class QuestionEvaluationForm(forms.ModelForm):
    class Meta:
        model = QuestionScore
        fields = ['awarded_marks', 'examiner_notes', 'feedback_to_student', 'is_draft']
        widgets = {
            'awarded_marks': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'examiner_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Internal confidential evaluation remarks...'}),
            'feedback_to_student': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Constructive feedback visible to candidate after results release...'}),
            'is_draft': forms.HiddenInput(),
        }
