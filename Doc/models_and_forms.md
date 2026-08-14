# Models & Forms Technical Breakdown — OptiExam Input Architecture
**Document Version:** 2.0.0  
**Audit:** 2026-08-14 — Added: Roster CSV import form, Tenant creation form, Result publication form, Grader allocation formset, expanded validation.

---

## 1. Authentication Forms

### 1.1 `OptiExamLoginForm`
```python
# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class OptiExamLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Username or email',
            'autocomplete': 'username', 'id': 'id-login-username',
            'aria-label': 'Username'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input', 'placeholder': 'Password',
            'autocomplete': 'current-password', 'id': 'id-login-password',
            'aria-label': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-remember-me'})
    )
```

---

## 2. Exam Blueprint & Configuration Forms

### 2.1 `ExamForm` — Main Exam Blueprint Creator
```python
# apps/exams/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from exams.models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'code', 'description', 'instructions', 'rules',
            'duration_minutes', 'start_time', 'end_time',
            'total_marks', 'passing_percentage',
            'allow_back_navigation', 'shuffle_questions', 'shuffle_options',
            'fullscreen_required', 'max_tab_violations', 'disable_copy_paste',
        ]
        widgets = {
            'title':              forms.TextInput(attrs={'class': 'form-input', 'id': 'id-exam-title'}),
            'code':               forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. CS-401-2026', 'id': 'id-exam-code'}),
            'description':        forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'instructions':       forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6, 'id': 'id-exam-instructions',
                                                        'placeholder': 'Instructions shown to candidates before starting...'}),
            'rules':              forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'duration_minutes':   forms.NumberInput(attrs={'class': 'form-input', 'min': 5, 'max': 360, 'id': 'id-duration'}),
            'start_time':         forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local', 'id': 'id-start-time'}),
            'end_time':           forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local', 'id': 'id-end-time'}),
            'total_marks':        forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5', 'id': 'id-total-marks'}),
            'passing_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': '1', 'min': '0', 'max': '100'}),
            'max_tab_violations': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time   = cleaned_data.get('start_time')
        end_time     = cleaned_data.get('end_time')
        duration     = cleaned_data.get('duration_minutes')

        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("Start Time must be before End Time.")
            if start_time < timezone.now():
                raise ValidationError("Start Time cannot be in the past.")
            window_mins = (end_time - start_time).total_seconds() / 60
            if duration and duration > window_mins:
                raise ValidationError(
                    f"Duration ({duration} min) cannot exceed the scheduling window ({int(window_mins)} min)."
                )
        return cleaned_data
```

### 2.2 `ExamLifelineConfigFormSet`
```python
from django.forms import inlineformset_factory
from exams.models import Exam, ExamLifelineConfig

ExamLifelineConfigFormSet = inlineformset_factory(
    Exam,
    ExamLifelineConfig,
    fields=['lifeline_type', 'is_enabled', 'max_allowed'],
    extra=0,
    can_delete=False,
    widgets={
        'lifeline_type': forms.Select(attrs={'class': 'form-select'}),
        'is_enabled':    forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'max_allowed':   forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
    }
)
```

---

---

## 3. Bulk Data Import Forms Suite

### 3.1 `ParticipantBatchImportForm`
```python
# apps/exams/forms.py
from django import forms
from django.core.exceptions import ValidationError

class ParticipantBatchImportForm(forms.Form):
    """
    Form for importing student exam rosters from CSV or Excel (.xlsx) files.
    """
    file = forms.FileField(
        label="Select Roster File (.CSV or .XLSX)",
        widget=forms.FileInput(attrs={
            'class': 'form-input-file',
            'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'id': 'id-roster-file',
            'aria-label': 'Upload Participant Roster File'
        }),
        help_text="Supported formats: .CSV, .XLSX (Max 5MB)"
    )
    overwrite_existing = forms.BooleanField(
        required=False,
        label="Overwrite existing candidate registrations in roster",
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-overwrite-roster'})
    )
    send_welcome_email = forms.BooleanField(
        required=False,
        initial=True,
        label="Send email notification with login credentials to new candidates",
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-send-email'})
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        valid_extensions = ('.csv', '.xlsx')
        if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
            raise ValidationError("Invalid file format. Please upload a .CSV or .XLSX file.")
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("File size exceeds 5MB limit.")
        return file
```

### 3.2 `QuestionBankImportForm`
```python
# apps/questions/forms.py
class QuestionBankImportForm(forms.Form):
    """
    Form for bulk importing questions, diagrams, model answers, and rubrics
    into a target QuestionBank from CSV, Excel, or ZIP bundle.
    """
    bank = forms.ModelChoiceField(
        queryset=None,  # Populated dynamically with request.tenant banks in __init__
        label="Target Question Bank",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-target-bank'})
    )
    file = forms.FileField(
        label="Upload Questions File (.CSV, .XLSX, or .ZIP with diagrams)",
        widget=forms.FileInput(attrs={
            'class': 'form-input-file',
            'accept': '.csv, .xlsx, .zip, application/zip',
            'id': 'id-question-import-file',
            'aria-label': 'Upload Question Bank File'
        }),
        help_text="Upload .CSV, .XLSX, or a .ZIP archive containing questions.csv and an images/ folder."
    )
    default_difficulty = forms.ChoiceField(
        choices=[('EASY', 'Easy'), ('MEDIUM', 'Medium'), ('HARD', 'Hard')],
        initial='MEDIUM',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-default-difficulty'})
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            from questions.models import QuestionBank
            self.fields['bank'].queryset = QuestionBank.objects.filter(tenant=tenant)

    def clean_file(self):
        file = self.cleaned_data['file']
        valid_extensions = ('.csv', '.xlsx', '.zip')
        if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
            raise ValidationError("Invalid file format. Please upload .CSV, .XLSX, or .ZIP.")
        if file.size > 25 * 1024 * 1024:  # 25MB for ZIP archives
            raise ValidationError("File size exceeds 25MB limit.")
        return file
```

### 3.3 `FacultyUserImportForm`
```python
# apps/accounts/forms.py
class FacultyUserImportForm(forms.Form):
    """
    Allows Designer / Super Admin to bulk import Item Writers, Graders, and faculty.
    """
    file = forms.FileField(
        label="Upload Faculty / Evaluators File (.CSV or .XLSX)",
        widget=forms.FileInput(attrs={
            'class': 'form-input-file',
            'accept': '.csv, .xlsx',
            'id': 'id-faculty-file'
        })
    )
    default_role = forms.ChoiceField(
        choices=[('ITEM_WRITER', 'Item Writer'), ('GRADER', 'Grader'), ('DESIGNER', 'Designer')],
        initial='ITEM_WRITER',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-default-role'})
    )
```

### 3.4 `ExamBlueprintImportForm`
```python
# apps/exams/forms.py
class ExamBlueprintImportForm(forms.Form):
    """
    Allows 1-click cloning and importing of entire Exam Blueprints from JSON/YAML.
    """
    file = forms.FileField(
        label="Upload Exam Blueprint (.JSON)",
        widget=forms.FileInput(attrs={'class': 'form-input-file', 'accept': '.json', 'id': 'id-blueprint-file'})
    )
    new_exam_code = forms.CharField(
        label="New Exam Code",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. CS-401-FALL-2026'})
    )
    new_start_time = forms.DateTimeField(
        label="New Scheduled Start Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'})
    )
```

---

## 4. Question Authoring Forms


### 4.1 `MCQQuestionForm` with Dynamic Option FormSet

```python
# apps/questions/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from questions.models import Question, QuestionOption, QuestionType

class MCQQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['bank', 'question_type', 'prompt', 'image_asset', 'points',
                  'negative_points', 'difficulty', 'blooms_level', 'hint_text', 'topic_tags']
        widgets = {
            'bank':          forms.Select(attrs={'class': 'form-select', 'id': 'id-question-bank'}),
            'question_type': forms.Select(attrs={'class': 'form-select', 'id': 'id-question-type'}),
            'prompt':        forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5, 'id': 'id-prompt',
                                                   'placeholder': 'Type your question statement...'}),
            'points':        forms.NumberInput(attrs={'class': 'form-input', 'step': '0.25', 'min': '0'}),
            'negative_points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.25', 'min': '0'}),
            'difficulty':    forms.Select(attrs={'class': 'form-select'}),
            'blooms_level':  forms.Select(attrs={'class': 'form-select'}),
            'hint_text':     forms.TextInput(attrs={'class': 'form-input',
                                                    'placeholder': 'Optional hint for Hint Token lifeline'}),
            'topic_tags':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. normalization, joins'}),
        }

class BaseOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        non_empty = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get('DELETE', False)]
        correct   = [f for f in non_empty if f.cleaned_data.get('is_correct', False)]

        if len(non_empty) < 2:
            raise ValidationError("At least 2 options are required for an MCQ.")
        
        question_type = self.instance.question_type if self.instance else None
        if question_type == QuestionType.MCQ_SINGLE and len(correct) != 1:
            raise ValidationError(f"Single-choice MCQ must have exactly 1 correct option. Found: {len(correct)}")
        elif question_type == QuestionType.MCQ_MULTIPLE and len(correct) < 1:
            raise ValidationError("Multiple-choice MCQ must have at least 1 correct option.")
        elif question_type == QuestionType.IMAGE_MCQ and len(correct) != 1:
            raise ValidationError("Image MCQ must have exactly 1 correct option.")

QuestionOptionFormSet = inlineformset_factory(
    Question, QuestionOption,
    formset=BaseOptionFormSet,
    fields=['option_text', 'option_image', 'is_correct', 'order', 'explanation'],
    extra=4, can_delete=True,
    widgets={
        'option_text':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Option text'}),
        'is_correct':   forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'order':        forms.NumberInput(attrs={'class': 'form-input-sm', 'min': 1}),
        'explanation':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Explanation (shown in review)'}),
    }
)
```

### 4.2 `ShortAnswerQuestionForm`
```python
class ShortAnswerQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['bank', 'prompt', 'points', 'word_limit', 'difficulty',
                  'blooms_level', 'model_answer', 'hint_text', 'topic_tags']
        widgets = {
            'prompt':       forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'word_limit':   forms.NumberInput(attrs={'class': 'form-input', 'min': 10, 'max': 500,
                                                     'placeholder': 'e.g. 150 words maximum'}),
            'model_answer': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5,
                                                  'placeholder': 'Model answer for Grader reference...'}),
        }
```

### 4.3 `LongEssayQuestionForm` with `RubricFormSet`
```python
from questions.models import QuestionRubric

class LongEssayQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['bank', 'prompt', 'image_asset', 'points', 'difficulty',
                  'blooms_level', 'model_answer', 'hint_text', 'topic_tags']
        widgets = {
            'prompt':       forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6}),
            'model_answer': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 10,
                                                  'placeholder': 'Detailed step-by-step model solution...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Validate that total rubric marks don't exceed question points (done in view after formset validation)
        return cleaned_data

QuestionRubricFormSet = inlineformset_factory(
    Question, QuestionRubric,
    fields=['criteria_title', 'description', 'max_points', 'order'],
    extra=3, can_delete=True,
    widgets={
        'criteria_title': forms.TextInput(attrs={'class': 'form-input',
                                                  'placeholder': 'e.g. Theoretical Accuracy'}),
        'description':    forms.TextInput(attrs={'class': 'form-input',
                                                  'placeholder': 'What does full marks look like?'}),
        'max_points':     forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
        'order':          forms.NumberInput(attrs={'class': 'form-input-sm', 'min': 1}),
    }
)
```

---

## 5. Grader Evaluation Forms

### 5.1 `QuestionScoreForm`
```python
# apps/grading/forms.py
from grading.models import QuestionScore

class QuestionScoreForm(forms.ModelForm):
    class Meta:
        model = QuestionScore
        fields = ['marks_awarded', 'grader_notes', 'feedback_to_student', 'is_draft']
        widgets = {
            'marks_awarded':       forms.NumberInput(attrs={
                'class': 'form-input scoring-input',
                'step': '0.25', 'min': '0',
                'id': 'id-marks-awarded',
                'aria-label': 'Marks Awarded'
            }),
            'grader_notes':        forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Private notes for Chief Examiner (not visible to student)...'
            }),
            'feedback_to_student': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Constructive feedback visible to student after result publication...'
            }),
            'is_draft':            forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-is-draft'}),
        }

    def clean_marks_awarded(self):
        marks = self.cleaned_data.get('marks_awarded')
        # max_marks is passed via form __init__ from the view
        max_marks = getattr(self, 'max_marks', None)
        if max_marks is not None and marks > max_marks:
            raise ValidationError(f"Marks awarded ({marks}) cannot exceed maximum ({max_marks}).")
        if marks < 0:
            raise ValidationError("Marks cannot be negative.")
        return marks
```

### 5.2 `GraderAllocationForm`
```python
from grading.models import GraderAllocation

class GraderAllocationForm(forms.ModelForm):
    class Meta:
        model = GraderAllocation
        fields = ['grader', 'candidate_range_start', 'candidate_range_end', 'section_scope', 'deadline']
        widgets = {
            'grader':                forms.Select(attrs={'class': 'form-select', 'id': 'id-grader'}),
            'candidate_range_start': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'id': 'id-range-start',
                                                              'placeholder': 'e.g. 1'}),
            'candidate_range_end':   forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'id': 'id-range-end',
                                                              'placeholder': 'e.g. 100'}),
            'section_scope':         forms.Select(attrs={'class': 'form-select'}),
            'deadline':              forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local',
                                                                'id': 'id-grader-deadline'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('candidate_range_start')
        end   = cleaned_data.get('candidate_range_end')
        if start and end and start > end:
            raise ValidationError("Range start must be less than or equal to range end.")
        return cleaned_data
```

---

## 6. Result Publication Form *(NEW — GAP-02 Resolution)*
```python
# apps/exams/forms.py
class ResultPublicationForm(forms.ModelForm):
    """
    Designer uses this form to explicitly release exam results to participants.
    """
    class Meta:
        model = Exam
        fields = ['results_published', 'show_grader_feedback']
        widgets = {
            'results_published':  forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-publish-results'}),
            'show_grader_feedback': forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-show-feedback'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('results_published') and not self.instance.pk:
            raise ValidationError("Cannot publish results for an unsaved exam.")
        return cleaned_data
```

---

## 7. Form Validation Summary

| Form | Key Validation Rules |
|---|---|
| `ExamForm` | `start_time < end_time`, `duration ≤ window`, `start_time not in past` |
| `MCQQuestionForm` + `BaseOptionFormSet` | Single: exactly 1 correct; Multiple: ≥ 1 correct; ≥ 2 options total |
| `LongEssayQuestionForm` + `RubricFormSet` | Sum of `rubric.max_points` ≤ `question.points` |
| `GraderAllocationForm` | `range_start ≤ range_end`, grader must belong to tenant, grader has `GRADER` role |
| `QuestionScoreForm` | `marks_awarded ≥ 0`, `marks_awarded ≤ question.points`, `is_draft` state-lock |
| `RosterCSVImportForm` | `.csv` extension only, size ≤ 5MB, valid headers required |
