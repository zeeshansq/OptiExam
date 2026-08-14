# Models & Forms Technical Breakdown — OptiExam Input Architecture
**Document Version:** 1.0.0  
**Project:** OptiExam Assessment Platform  
**Document Scope:** Complete guide to Django Forms, FormSets, Custom Widgets, Validation Hooks, and Input Handling across the 5 User Roles.

---

## 1. Authentication & User Management Forms

### 1.1 `OptiExamLoginForm`
Provides a universal, secure login interface for all 5 user tiers with automated tenant resolution.

```python
# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm

class OptiExamLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username',
            'id': 'login-username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'id': 'login-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
```

---

## 2. Exam Blueprint & Configuration Forms

### 2.1 `ExamForm`
Used by the Designer (Tenant Admin) to create and configure comprehensive examination blueprints.

```python
# exams/forms.py
from django import forms
from django.core.exceptions import ValidationError
from exams.models import Exam

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'code', 'description', 'instructions', 'rules',
            'duration_minutes', 'start_time', 'end_time',
            'total_marks', 'passing_percentage',
            'allow_back_navigation', 'shuffle_questions', 'shuffle_options',
            'fullscreen_required', 'max_tab_violations'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Fall Semester Final: Database Systems'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. CS-401-2026'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'instructions': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Rules displayed before starting...'}),
            'rules': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-input', 'min': 5, 'max': 360}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'passing_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': '1'}),
            'max_tab_violations': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        duration_minutes = cleaned_data.get('duration_minutes')

        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("Exam Start Time must be strictly earlier than End Time.")
            
            window_minutes = (end_time - start_time).total_seconds() / 60
            if duration_minutes and duration_minutes > window_minutes:
                raise ValidationError(f"Allowed duration ({duration_minutes}m) cannot exceed the total scheduling window ({int(window_minutes)}m).")
        return cleaned_data
```

### 2.2 `ExamLifelineConfigFormSet`
Inline formset enabling the Designer to toggle and configure specific lifelines per exam.

```python
# exams/forms.py
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
        'is_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'max_allowed': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'max': 10}),
    }
)
```

---

## 3. Question Authoring Forms & Dynamic Widgets

### 3.1 MCQ Question Form with Dynamic Options FormSet

```python
# questions/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from questions.models import Question, QuestionOption, QuestionType

class MCQQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['bank', 'section', 'question_type', 'prompt', 'points', 'negative_points', 'difficulty', 'hint_text']
        widgets = {
            'bank': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'prompt': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Type your question statement...'}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
            'negative_points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.25'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'hint_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional hint for Hint Token lifeline'}),
        }

class BaseQuestionOptionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        
        correct_count = 0
        non_empty_options = 0
        
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                non_empty_options += 1
                if form.cleaned_data.get('is_correct', False):
                    correct_count += 1
        
        if non_empty_options < 2:
            raise ValidationError("An MCQ question must provide at least 2 options.")
        
        # Validate based on single vs multiple choice
        question_type = self.instance.question_type if self.instance else None
        if question_type == QuestionType.MCQ_SINGLE and correct_count != 1:
            raise ValidationError(f"Single Choice MCQ must have exactly 1 correct option. Found {correct_count}.")
        elif question_type == QuestionType.MCQ_MULTIPLE and correct_count < 1:
            raise ValidationError("Multiple Choice MCQ must have at least 1 correct option.")

QuestionOptionFormSet = inlineformset_factory(
    Question,
    QuestionOption,
    formset=BaseQuestionOptionFormSet,
    fields=['option_text', 'option_image', 'is_correct', 'order', 'explanation'],
    extra=4,
    can_delete=True,
    widgets={
        'option_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Option text'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'order': forms.NumberInput(attrs={'class': 'form-input-sm', 'min': 1}),
        'explanation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Explanation for review'}),
    }
)
```

### 3.2 Long Essay & Rubric Matrix Authoring Form

```python
# questions/forms.py
from questions.models import QuestionRubric

class LongEssayQuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['bank', 'section', 'prompt', 'points', 'difficulty', 'model_answer', 'hint_text']
        widgets = {
            'prompt': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6}),
            'model_answer': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 8, 'placeholder': 'Detailed model solution for Graders...'}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'step': '1.0'}),
        }

QuestionRubricFormSet = inlineformset_factory(
    Question,
    QuestionRubric,
    fields=['criteria_title', 'description', 'max_points', 'order'],
    extra=3,
    can_delete=True,
    widgets={
        'criteria_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Theoretical Accuracy'}),
        'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Scoring instructions for grader'}),
        'max_points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5'}),
        'order': forms.NumberInput(attrs={'class': 'form-input-sm'}),
    }
)
```

---

## 4. Grader Evaluation Forms

### 4.1 `QuestionScoreForm`
Used inside the split-screen evaluation studio for grading subjective short/long questions.

```python
# grading/forms.py
from django import forms
from grading.models import QuestionScore

class QuestionScoreForm(forms.ModelForm):
    class Meta:
        model = QuestionScore
        fields = ['marks_awarded', 'grader_notes', 'feedback_to_student', 'is_draft']
        widgets = {
            'marks_awarded': forms.NumberInput(attrs={
                'class': 'form-input scoring-slider-input',
                'step': '0.25',
                'min': '0'
            }),
            'grader_notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 2,
                'placeholder': 'Confidential notes for Chief Examiner / Moderation...'
            }),
            'feedback_to_student': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Constructive feedback visible to the student...'
            }),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
```

### 4.2 `GraderAllocationForm`
Allows the Designer to assign candidate batches (e.g. 1–100, 101–200) to specific graders.

```python
# grading/forms.py
from django import forms
from grading.models import GraderAllocation

class GraderAllocationForm(forms.ModelForm):
    class Meta:
        model = GraderAllocation
        fields = ['grader', 'candidate_range_start', 'candidate_range_end', 'deadline']
        widgets = {
            'grader': forms.Select(attrs={'class': 'form-select'}),
            'candidate_range_start': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'e.g. 1'}),
            'candidate_range_end': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'e.g. 100'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }
```
