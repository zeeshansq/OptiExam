from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .models import QuestionBank, Question, QuestionOption, QuestionRubric

class QuestionBankForm(forms.ModelForm):
    class Meta:
        model = QuestionBank
        fields = ['name', 'code', 'subject', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Computer Science Fundamentals'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. CS101-BANK'}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Data Structures & Algorithms'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Optional description of topics covered...'}),
        }


class QuestionBankFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search banks by name, code, subject...'
        })
    )
    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Filter by subject...'
        })
    )


class QuestionFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search question text, keywords, tags...'
        })
    )
    question_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Question Formats')] + list(Question.QuestionType.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    difficulty = forms.ChoiceField(
        required=False,
        choices=[('', 'All Difficulties')] + list(Question.Difficulty.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    blooms_level = forms.ChoiceField(
        required=False,
        choices=[('', "All Bloom's Levels")] + list(Question.BloomsLevel.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class QuestionBaseForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            'bank', 'question_type', 'prompt', 'image_asset',
            'points', 'negative_points', 'difficulty', 'blooms_level',
            'topic_tags', 'model_answer', 'hint_text'
        ]
        widgets = {
            'bank': forms.Select(attrs={'class': 'form-select'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'prompt': forms.Textarea(attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Type your question prompt here...'}),
            'image_asset': forms.FileInput(attrs={'class': 'form-input', 'id': 'id_image_asset', 'accept': 'image/*'}),
            'points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5', 'min': '0.5'}),
            'negative_points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.25', 'min': '0.0'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'blooms_level': forms.Select(attrs={'class': 'form-select'}),
            'topic_tags': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. arrays, sorting, oop'}),
            'model_answer': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Confidential scoring guidance for graders...'}),
            'hint_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional hint revealed via Hint Token lifeline...'}),
        }


    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['bank'].queryset = QuestionBank.objects.for_tenant(tenant)


class BaseQuestionOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        valid_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]

        if not valid_forms:
            raise ValidationError("At least 2 choices are required for multiple-choice questions.")

        correct_count = sum(1 for form in valid_forms if form.cleaned_data.get('is_correct', False))
        q_type = self.instance.question_type if self.instance else None

        if q_type == Question.QuestionType.MCQ_SINGLE or q_type == Question.QuestionType.IMAGE_MCQ:
            if correct_count != 1:
                raise ValidationError(f"Single Choice MCQ must have exactly 1 correct answer (currently {correct_count} selected).")
        elif q_type == Question.QuestionType.MCQ_MULTIPLE:
            if correct_count < 1:
                raise ValidationError("Multiple Choice MCQ must have at least 1 correct answer marked.")


QuestionOptionFormSet = inlineformset_factory(
    Question,
    QuestionOption,
    formset=BaseQuestionOptionFormSet,
    fields=['option_text', 'is_correct', 'order', 'explanation'],
    widgets={
        'option_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Option text'}),
        'is_correct': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        'order': forms.HiddenInput(),
        'explanation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional rationale'}),
    },
    extra=4,
    can_delete=True
)


class BaseQuestionRubricFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        valid_forms = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]

        if not valid_forms:
            return

        total_rubric_points = sum(form.cleaned_data.get('max_points', 0) for form in valid_forms)
        if self.instance and self.instance.points and total_rubric_points > self.instance.points:
            raise ValidationError(
                f"Sum of rubric criteria ({total_rubric_points} pts) exceeds total question marks ({self.instance.points} pts)."
            )


QuestionRubricFormSet = inlineformset_factory(
    Question,
    QuestionRubric,
    formset=BaseQuestionRubricFormSet,
    fields=['criteria_title', 'description', 'max_points', 'order'],
    widgets={
        'criteria_title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Criterion (e.g. Methodology)'}),
        'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Grading guideline'}),
        'max_points': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.5', 'min': '0.5'}),
        'order': forms.HiddenInput(),
    },
    extra=2,
    can_delete=True
)


class QuestionImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv,.xlsx,.zip'}),
        help_text="Upload .CSV, .XLSX, or .ZIP archive (containing CSV + diagrams)"
    )
