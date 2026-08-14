from django.test import TestCase, Client
from django.urls import reverse
from apps.tenants.models import Tenant, TenantFeatureFlag
from apps.accounts.models import User, UserRole, AuditLog
from apps.tenants.services.tenant_service import create_tenant, toggle_feature_flag

class TenantCRUDAndFilteringTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.super_admin = User.objects.create_superuser(
            username="sa_manager",
            email="sa@optiexam.local",
            password="AdminPassword123!",
            role=UserRole.SUPER_ADMIN
        )
        self.client.force_login(self.super_admin)

        # Create multiple test institutions for pagination/filter tests
        self.tenant1 = Tenant.objects.create(name="Alpha Institute", slug="alpha", tier=Tenant.Tier.STARTER, is_active=True)
        self.tenant2 = Tenant.objects.create(name="Beta College", slug="beta", tier=Tenant.Tier.PROFESSIONAL, is_active=True)
        self.tenant3 = Tenant.objects.create(name="Gamma University", slug="gamma", tier=Tenant.Tier.ENTERPRISE, is_active=False)

    def test_super_admin_dashboard_search(self):
        """Verify search filters by institution name and slug."""
        response = self.client.get(reverse('tenants:super_admin_dashboard'), {'q': 'Alpha'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Institute")
        self.assertNotContains(response, "Beta College")

    def test_super_admin_dashboard_tier_filter(self):
        """Verify tier filtering returns only matching institutions."""
        response = self.client.get(reverse('tenants:super_admin_dashboard'), {'tier': 'ENTERPRISE'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gamma University")
        self.assertNotContains(response, "Alpha Institute")

    def test_super_admin_dashboard_status_filter(self):
        """Verify active/inactive filtering."""
        response = self.client.get(reverse('tenants:super_admin_dashboard'), {'status': 'inactive'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gamma University")
        self.assertNotContains(response, "Alpha Institute")

    def test_tenant_create_view(self):
        """Verify provisioning a new institution creates tenant and default flags."""
        response = self.client.post(reverse('tenants:tenant_create'), {
            'name': 'Delta Polytechnic',
            'slug': 'delta',
            'tier': 'PROFESSIONAL',
            'max_concurrent_candidates': 300,
            'primary_color': '#10B981',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        tenant = Tenant.objects.get(slug='delta')
        self.assertEqual(tenant.name, 'Delta Polytechnic')
        self.assertEqual(tenant.feature_flags.count(), 7)

    def test_tenant_update_view(self):
        """Verify editing institution settings."""
        response = self.client.post(reverse('tenants:tenant_update', kwargs={'pk': self.tenant1.pk}), {
            'name': 'Alpha Institute Updated',
            'slug': 'alpha',
            'tier': 'ENTERPRISE',
            'max_concurrent_candidates': 800,
            'primary_color': '#8B5CF6',
            'is_active': True,
        })
        self.assertEqual(response.status_code, 302)
        self.tenant1.refresh_from_db()
        self.assertEqual(self.tenant1.name, 'Alpha Institute Updated')
        self.assertEqual(self.tenant1.max_concurrent_candidates, 800)

    def test_tenant_delete_view(self):
        """Verify safe deactivation / removal of institution."""
        response = self.client.post(reverse('tenants:tenant_delete', kwargs={'pk': self.tenant3.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tenant.objects.filter(pk=self.tenant3.pk).exists())

    def test_tenant_feature_flag_toggle_ajax(self):
        """Verify AJAX feature flag toggle endpoint."""
        flag = TenantFeatureFlag.objects.create(
            tenant=self.tenant1,
            feature_key=TenantFeatureFlag.Feature.LIVE_PROCTORING,
            is_enabled=True
        )
        response = self.client.post(
            reverse('tenants:tenant_flag_toggle', kwargs={'pk': self.tenant1.pk, 'feature_key': 'LIVE_PROCTORING'}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['is_enabled'])

    def test_audit_logs_explorer_view(self):
        """Verify audit logs explorer view renders with search and category filters."""
        AuditLog.objects.create(
            tenant=self.tenant1,
            user=self.super_admin,
            action="Test Administrative Operation",
            category=AuditLog.ActionCategory.ADMIN_OP,
            ip_address="127.0.0.1"
        )
        response = self.client.get(reverse('tenants:audit_logs'), {'category': 'ADMIN_OP'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Administrative Operation")
