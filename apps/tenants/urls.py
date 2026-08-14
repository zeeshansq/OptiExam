from django.urls import path
from apps.tenants.views import tenant_views
from apps.accounts.views import auth_views

app_name = 'tenants'

urlpatterns = [
    # SaaS Super Admin Operations & Full CRUD
    path('admin/saas/dashboard/', tenant_views.SuperAdminDashboardView.as_view(), name='super_admin_dashboard'),
    path('admin/saas/create/', tenant_views.TenantCreateView.as_view(), name='tenant_create'),
    path('admin/saas/<int:pk>/', tenant_views.TenantDetailView.as_view(), name='tenant_detail'),
    path('admin/saas/<int:pk>/edit/', tenant_views.TenantUpdateView.as_view(), name='tenant_update'),
    path('admin/saas/<int:pk>/delete/', tenant_views.TenantDeleteView.as_view(), name='tenant_delete'),
    path('admin/saas/<int:pk>/flag/<str:feature_key>/toggle/', tenant_views.TenantFeatureFlagToggleView.as_view(), name='tenant_flag_toggle'),
    path('admin/saas/audit-logs/', tenant_views.AuditLogListView.as_view(), name='audit_logs'),

    # Tenant-Scoped Dashboards (Phase 1 Baseline)
    path('<slug:tenant_slug>/dashboard/', auth_views.DesignerDashboardView.as_view(), name='designer_dashboard'),
    path('<slug:tenant_slug>/questions/', auth_views.ItemWriterDashboardView.as_view(), name='item_writer_dashboard'),
    path('<slug:tenant_slug>/grading/', auth_views.GraderDashboardView.as_view(), name='grader_dashboard'),
    path('<slug:tenant_slug>/lobby/', auth_views.ParticipantDashboardView.as_view(), name='participant_dashboard'),
]
