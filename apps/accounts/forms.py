from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.accounts.models import User, UserProfile

class OptiExamLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username or Email',
            'autocomplete': 'username',
            'id': 'id-login-username',
            'aria-label': 'Username'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'id': 'id-login-password',
            'aria-label': 'Password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id-remember-me'})
    )

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model = UserProfile
        fields = ['registration_number', 'department', 'batch_year', 'specialization', 'bio']
        widgets = {
            'registration_number': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'batch_year': forms.TextInput(attrs={'class': 'form-input'}),
            'specialization': forms.TextInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

class FacultyUserImportForm(forms.Form):
    """
    Allows Designer / Super Admin to bulk import Item Writers, Graders, and faculty from CSV/XLSX.
    """
    file = forms.FileField(
        label="Upload Faculty File (.CSV or .XLSX)",
        widget=forms.FileInput(attrs={
            'class': 'form-input-file',
            'accept': '.csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'id': 'id-faculty-file'
        }),
        help_text="Expected columns: username, first_name, last_name, email, role (ITEM_WRITER|GRADER), department"
    )
    default_role = forms.ChoiceField(
        choices=[('ITEM_WRITER', 'Item Writer'), ('GRADER', 'Grader'), ('DESIGNER', 'Designer')],
        initial='ITEM_WRITER',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-default-role'})
    )
