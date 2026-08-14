from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from apps.tenants.models import Tenant, TenantFeatureFlag
from apps.tenants.forms import TenantForm, TenantUpdateForm, TenantFilterForm, AuditLogFilterForm
from apps.tenants.services.tenant_service import initialize_default_feature_flags, toggle_feature_flag
from apps.accounts.models import AuditLog, User
from apps.accounts.services.auth_service import record_audit_log
from apps.core.mixins import SuperAdminRequiredMixin

class SuperAdminDashboardView(SuperAdminRequiredMixin, ListView):
    """
    High-density SaaS management matrix with advanced multi-field search,
    tier/status filters, two-way clickable column sorting, and full-featured pagination.
    """
    model = Tenant
    template_name = 'dashboards/super_admin.html'
    context_object_name = 'tenants'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size')
        if page_size in ['10', '25', '50', '100']:
            return int(page_size)
        return self.paginate_by

    def get_queryset(self):
        qs = Tenant.objects.all()
        q = self.request.GET.get('q', '').strip()
        tier = self.request.GET.get('tier', '').strip()
        status = self.request.GET.get('status', '').strip()
        sort = self.request.GET.get('sort', '').strip()
        order = self.request.GET.get('order', 'asc').strip()

        # 1. Advanced Full-Text Search
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(slug__icontains=q) |
                Q(domain__icontains=q) |
                Q(contact_email__icontains=q)
            )

        # 2. Tier Filter
        if tier:
            qs = qs.filter(tier=tier)

        # 3. Status Filter
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        # 4. Multi-Column Clickable Sorting
        allowed_sorts = ['name', 'slug', 'tier', 'max_concurrent_candidates', 'is_active', 'created_at']
        if sort in allowed_sorts:
            prefix = '-' if order == 'desc' else ''
            qs = qs.order_by(f"{prefix}{sort}")
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_tenants = Tenant.objects.all()
        ctx['total_tenants'] = all_tenants.count()
        ctx['active_tenants'] = all_tenants.filter(is_active=True).count()
        ctx['starter_count'] = all_tenants.filter(tier=Tenant.Tier.STARTER).count()
        ctx['professional_count'] = all_tenants.filter(tier=Tenant.Tier.PROFESSIONAL).count()
        ctx['enterprise_count'] = all_tenants.filter(tier=Tenant.Tier.ENTERPRISE).count()

        # Pass filter form bound to GET params
        ctx['filter_form'] = TenantFilterForm(self.request.GET)
        ctx['active_search_query'] = self.request.GET.get('q', '')
        ctx['active_tier_filter'] = self.request.GET.get('tier', '')
        ctx['active_status_filter'] = self.request.GET.get('status', '')
        return ctx

class TenantCreateView(SuperAdminRequiredMixin, CreateView):
    """
    Categorized institution provisioning wizard with prefilled defaults.
    """
    model = Tenant
    form_class = TenantForm
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenants:super_admin_dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Auto-initialize 7 default feature flags
        initialize_default_feature_flags(self.object)
        
        record_audit_log(
            action=f"Provisioned new institution '{self.object.name}' ({self.object.slug})",
            category=AuditLog.ActionCategory.ADMIN_OP,
            user=self.request.user,
            tenant=self.object,
            request=self.request,
            payload={'tenant_id': self.object.id, 'tier': self.object.tier, 'slug': self.object.slug}
        )
        messages.success(self.request, f"Institution '{self.object.name}' provisioned successfully!")
        return response

class TenantUpdateView(SuperAdminRequiredMixin, UpdateView):
    """
    Comprehensive institution settings & quota editor.
    """
    model = Tenant
    form_class = TenantUpdateForm
    template_name = 'tenants/tenant_form.html'
    context_object_name = 'tenant_obj'

    def get_success_url(self):
        return reverse('tenants:tenant_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        record_audit_log(
            action=f"Updated settings for institution '{self.object.name}'",
            category=AuditLog.ActionCategory.ADMIN_OP,
            user=self.request.user,
            tenant=self.object,
            request=self.request
        )
        messages.success(self.request, f"Settings for '{self.object.name}' updated successfully.")
        return response

class TenantDetailView(SuperAdminRequiredMixin, DetailView):
    """
    Deep inspection cockpit for institution quotas, users, and feature flags.
    """
    model = Tenant
    template_name = 'tenants/tenant_detail.html'
    context_object_name = 'tenant_obj'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['feature_flags'] = self.object.feature_flags.all().order_by('feature_key')
        ctx['tenant_users_count'] = User.objects.filter(tenant=self.object).count()
        ctx['recent_tenant_logs'] = AuditLog.objects.filter(tenant=self.object)[:10]
        return ctx

class TenantDeleteView(SuperAdminRequiredMixin, DeleteView):
    """
    Safe soft-deactivation or deletion of institution with confirmation.
    """
    model = Tenant
    template_name = 'tenants/tenant_confirm_delete.html'
    context_object_name = 'tenant_obj'
    success_url = reverse_lazy('tenants:super_admin_dashboard')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        tenant_name = self.object.name
        record_audit_log(
            action=f"Deleted/Deactivated institution '{tenant_name}' ({self.object.slug})",
            category=AuditLog.ActionCategory.ADMIN_OP,
            user=request.user,
            request=request
        )
        messages.warning(request, f"Institution '{tenant_name}' has been removed.")
        return super().delete(request, *args, **kwargs)

class TenantFeatureFlagToggleView(SuperAdminRequiredMixin, View):
    """
    AJAX endpoint for 1-click feature flag toggling.
    """
    def post(self, request, pk, feature_key, *args, **kwargs):
        tenant = get_object_or_404(Tenant, pk=pk)
        flag = toggle_feature_flag(tenant, feature_key)
        
        record_audit_log(
            action=f"Toggled feature flag '{feature_key}' to {flag.is_enabled} for '{tenant.name}'",
            category=AuditLog.ActionCategory.ADMIN_OP,
            user=request.user,
            tenant=tenant,
            request=request
        )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'status': 'success', 'feature_key': feature_key, 'is_enabled': flag.is_enabled})
        messages.success(request, f"Feature flag '{flag.get_feature_key_display()}' set to {'Enabled' if flag.is_enabled else 'Disabled'}.")
        return redirect('tenants:tenant_detail', pk=pk)

class AuditLogListView(SuperAdminRequiredMixin, ListView):
    """
    Global and tenant-filtered Audit Log Explorer with category pills and search.
    """
    model = AuditLog
    template_name = 'tenants/audit_logs.html'
    context_object_name = 'audit_logs'
    paginate_by = 15

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size')
        if page_size in ['15', '30', '50', '100']:
            return int(page_size)
        return self.paginate_by

    def get_queryset(self):
        qs = AuditLog.objects.select_related('user', 'tenant').all()
        q = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '').strip()

        if q:
            qs = qs.filter(
                Q(action__icontains=q) |
                Q(ip_address__icontains=q) |
                Q(user__username__icontains=q) |
                Q(tenant__name__icontains=q)
            )

        if category:
            qs = qs.filter(category=category)

        return qs.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = AuditLogFilterForm(self.request.GET)
        ctx['active_search_query'] = self.request.GET.get('q', '')
        ctx['active_category_filter'] = self.request.GET.get('category', '')
        return ctx
