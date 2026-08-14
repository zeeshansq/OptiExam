from django import forms
from django.forms import inlineformset_factory
from apps.tenants.models import Tenant, TenantFeatureFlag
from apps.accounts.models import AuditLog

class TenantForm(forms.ModelForm):
    """
    Categorized form with prefilled defaults, color palettes, and auto-slug target.
    """
    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'domain', 'tier', 'max_concurrent_candidates',
            'primary_color', 'contact_email', 'logo', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'id': 'id-tenant-name',
                'placeholder': 'e.g. National Engineering College',
                'required': True
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-input font-mono',
                'id': 'id-tenant-slug',
                'placeholder': 'e.g. nec',
                'required': True
            }),
            'domain': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. exams.nec.edu (Optional)'
            }),
            'tier': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id-tenant-tier'
            }),
            'max_concurrent_candidates': forms.NumberInput(attrs={
                'class': 'form-input',
                'id': 'id-max-candidates',
                'min': 10,
                'max': 100000,
                'placeholder': '500'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'color',
                'id': 'id-primary-color'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'dean.exams@institution.edu'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-input-file',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'id': 'id-tenant-active'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supply sensible prefilled defaults for new institutions
        if not self.instance.pk:
            self.fields['tier'].initial = Tenant.Tier.PROFESSIONAL
            self.fields['max_concurrent_candidates'].initial = 500
            self.fields['primary_color'].initial = '#4F46E5'
            self.fields['is_active'].initial = True

class TenantUpdateForm(TenantForm):
    """Form for updating an existing institution."""
    pass

class TenantFilterForm(forms.Form):
    """
    Advanced search and multi-filter toolbar for Super Admin Institution Directory.
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input search-input',
            'placeholder': 'Search institution name, slug, domain...',
            'id': 'id-tenant-search'
        })
    )
    tier = forms.ChoiceField(
        choices=[('', 'All Tiers')] + list(Tenant.Tier.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-filter-tier'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses'), ('active', 'Active Only'), ('inactive', 'Suspended Only')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-filter-status'})
    )
    page_size = forms.ChoiceField(
        choices=[('10', '10 / page'), ('25', '25 / page'), ('50', '50 / page'), ('100', '100 / page')],
        initial='10',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-page-size'})
    )

class AuditLogFilterForm(forms.Form):
    """
    Advanced search & filter toolbar for Audit Log Explorer.
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input search-input',
            'placeholder': 'Search action, user, IP...',
            'id': 'id-audit-search'
        })
    )
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + list(AuditLog.ActionCategory.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id-audit-category'})
    )
    page_size = forms.ChoiceField(
        choices=[('15', '15 / page'), ('30', '30 / page'), ('50', '50 / page'), ('100', '100 / page')],
        initial='15',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

TenantFeatureFlagFormSet = inlineformset_factory(
    Tenant,
    TenantFeatureFlag,
    fields=['feature_key', 'is_enabled'],
    extra=0,
    can_delete=False,
    widgets={
        'feature_key': forms.Select(attrs={'class': 'form-select'}),
        'is_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    }
)
