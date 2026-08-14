from django.test import TestCase, Client
from django.urls import reverse
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole, AuditLog
from apps.accounts.services.auth_service import get_redirect_url_for_user

class AuthAndRoleRedirectionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant = Tenant.objects.create(name="Medical University", slug="med-uni")

        self.super_admin = User.objects.create_superuser(
            username="sa_admin",
            email="sa@optiexam.local",
            password="Password123!",
            role=UserRole.SUPER_ADMIN
        )
        self.designer = User.objects.create_user(
            username="des_user",
            email="des@med.edu",
            password="Password123!",
            tenant=self.tenant,
            role=UserRole.DESIGNER
        )
        self.student = User.objects.create_user(
            username="stu_user",
            email="stu@med.edu",
            password="Password123!",
            tenant=self.tenant,
            role=UserRole.PARTICIPANT
        )

    def test_role_redirect_urls(self):
        """Verify role redirect URLs resolve properly per role."""
        sa_url = get_redirect_url_for_user(self.super_admin)
        self.assertEqual(sa_url, reverse('tenants:super_admin_dashboard'))

        des_url = get_redirect_url_for_user(self.designer)
        self.assertEqual(des_url, reverse('tenants:designer_dashboard', kwargs={'tenant_slug': 'med-uni'}))

        stu_url = get_redirect_url_for_user(self.student)
        self.assertEqual(stu_url, reverse('tenants:participant_dashboard', kwargs={'tenant_slug': 'med-uni'}))

    def test_login_flow_and_audit_logging(self):
        """Verify login sets session and creates audit log."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'des_user',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify audit log created
        log = AuditLog.objects.filter(user=self.designer, category=AuditLog.ActionCategory.AUTH).first()
        self.assertIsNotNone(log)
        self.assertIn('logged in successfully', log.action)
