from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Exam, ExamSection, ExamQuestionAssignment, ExamLifelineConfig, ExamParticipantRoster
from apps.questions.models import Question, QuestionBank

class ExamFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search exams by title, code, subject...'
        })
    )
    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Filter by subject...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses'), ('active', 'Active'), ('published', 'Results Released'), ('draft', 'Draft / Inactive')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ExamBlueprintForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'code', 'subject', 'description', 'instructions',
            'start_time', 'end_time', 'duration_minutes', 'total_marks', 'passing_percentage',
            'enforce_fullscreen', 'max_tab_switch_limit', 'lock_copy_paste',
            'shuffle_questions', 'shuffle_options', 'allow_back_navigation',
            'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Midterm Assessment: Algorithms'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. CS101-MID-2026'}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Computer Science'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Overview for candidates...'}),
            'instructions': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Rules displayed in the exam lobby before starting...'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input', 'min': '5', 'step': '5'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'step': '1'}),
            'passing_percentage': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'max': '100', 'step': '1'}),
            'max_tab_switch_limit': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'max': '10'}),
            'enforce_fullscreen': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'lock_copy_paste': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'shuffle_options': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'allow_back_navigation': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        duration = cleaned_data.get('duration_minutes')

        if start and end:
            if end <= start:
                raise ValidationError("Exam window End Time must be later than Start Time.")

            window_minutes = (end - start).total_seconds() / 60
            if duration and duration > window_minutes:
                raise ValidationError(
                    f"Candidate duration ({duration} mins) exceeds total schedule window ({int(window_minutes)} mins)."
                )

        return cleaned_data


class BaseExamSectionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        valid_forms = [
            f for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
        ]

        if not valid_forms:
            raise ValidationError("An exam blueprint must contain at least 1 section.")


ExamSectionFormSet = inlineformset_factory(
    Exam,
    ExamSection,
    formset=BaseExamSectionFormSet,
    fields=['title', 'description', 'order', 'weightage'],
    widgets={
        'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Section A: Objective MCQs'}),
        'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Section guidance'}),
        'order': forms.NumberInput(attrs={'class': 'form-input', 'style': 'width: 70px;'}),
        'weightage': forms.NumberInput(attrs={'class': 'form-input', 'step': '1.0', 'style': 'width: 100px;'}),
    },
    extra=2,
    can_delete=True
)


class BaseExamLifelineConfigFormSet(BaseInlineFormSet):
    pass

ExamLifelineConfigFormSet = inlineformset_factory(
    Exam,
    ExamLifelineConfig,
    formset=BaseExamLifelineConfigFormSet,
    fields=['lifeline_type', 'is_enabled', 'max_allowed'],
    widgets={
        'lifeline_type': forms.Select(attrs={'class': 'form-select'}),
        'is_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'max_allowed': forms.NumberInput(attrs={'class': 'form-input', 'min': '1', 'max': '5', 'style': 'width: 90px;'}),
    },
    extra=0,
    can_delete=False
)



class QuestionAssignForm(forms.Form):
    section_id = forms.IntegerField(widget=forms.HiddenInput())
    question_id = forms.IntegerField(widget=forms.HiddenInput())
    order = forms.IntegerField(required=False, initial=1)
    custom_marks = forms.DecimalField(required=False, max_digits=6, decimal_places=2)
    is_reserve = forms.BooleanField(required=False, initial=False)



class RosterCSVImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv,.xlsx'}),
        help_text="Select a valid Candidate Roster spreadsheet (.CSV or .XLSX)."
    )


class CandidateEnrollmentForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Alex'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Johnson'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'alex.johnson@institution.edu'})
    )
    registration_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. REG-2026-042'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Computer Science'})
    )
    batch_year = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 2026'})
    )
    status = forms.ChoiceField(
        choices=ExamParticipantRoster.Status.choices,
        initial=ExamParticipantRoster.Status.ENROLLED,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CandidateEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    batch_year = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = ExamParticipantRoster
        fields = ['registration_number', 'status']
        widgets = {
            'registration_number': forms.TextInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.participant:
            self.fields['first_name'].initial = self.instance.participant.first_name
            self.fields['last_name'].initial = self.instance.participant.last_name
            self.fields['email'].initial = self.instance.participant.email
            if hasattr(self.instance.participant, 'profile'):
                self.fields['department'].initial = self.instance.participant.profile.department
                self.fields['batch_year'].initial = self.instance.participant.profile.batch_year


class RosterFilterForm(forms.Form):

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search candidate name, reg #, email...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(ExamParticipantRoster.Status.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

