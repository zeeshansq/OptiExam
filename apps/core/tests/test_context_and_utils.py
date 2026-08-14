from django.test import TestCase, RequestFactory
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole
from apps.core.context_processors import (
    tenant_context, user_role_context, notification_context,
    active_exam_context, system_settings_context
)
from apps.core.utils import generate_secure_token, generate_candidate_seed
from apps.core.permissions import IsSuperAdmin, IsTenantDesigner, IsItemWriter, IsGrader, IsParticipant

class ContextProcessorsAndUtilsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(name="Apex Academy", slug="apex", primary_color="#10B981")
        self.super_admin = User.objects.create_superuser(username="super", role=UserRole.SUPER_ADMIN)
        self.designer = User.objects.create_user(username="des_apex", tenant=self.tenant, role=UserRole.DESIGNER)
        self.student = User.objects.create_user(username="stu_apex", tenant=self.tenant, role=UserRole.PARTICIPANT)

    def test_tenant_context_processor(self):
        request = self.factory.get('/')
        request.user = self.designer
        request.tenant = self.tenant
        
        ctx = tenant_context(request)
        self.assertEqual(ctx['tenant_name'], "Apex Academy")
        self.assertEqual(ctx['tenant_slug'], "apex")
        self.assertEqual(ctx['tenant_primary_color'], "#10B981")

    def test_user_role_context_processor(self):
        request = self.factory.get('/')
        request.user = self.designer
        
        ctx = user_role_context(request)
        self.assertTrue(ctx['is_designer'])
        self.assertFalse(ctx['is_participant'])
        self.assertEqual(ctx['user_role_name'], "Designer (Tenant Admin)")

    def test_system_settings_context_processor(self):
        request = self.factory.get('/')
        request.user = self.designer
        request.session = {'ui_theme': 'light'}
        
        ctx = system_settings_context(request)
        self.assertTrue(ctx['IS_OFFLINE_READY'])
        self.assertEqual(ctx['ui_theme'], 'light')
        self.assertFalse(ctx['is_dark_mode'])

    def test_utils_token_and_seed_generation(self):
        token = generate_secure_token(16)
        self.assertEqual(len(token), 32)
        
        seed1 = generate_candidate_seed(101, 5)
        seed2 = generate_candidate_seed(101, 5)
        seed3 = generate_candidate_seed(102, 5)
        
        self.assertEqual(seed1, seed2)
        self.assertNotEqual(seed1, seed3)

    def test_drf_permissions(self):
        request = self.factory.get('/')
        request.tenant = self.tenant
        
        request.user = self.super_admin
        self.assertTrue(IsSuperAdmin().has_permission(request, None))
        
        request.user = self.designer
        self.assertTrue(IsTenantDesigner().has_permission(request, None))
        self.assertFalse(IsSuperAdmin().has_permission(request, None))
        
        request.user = self.student
        self.assertTrue(IsParticipant().has_permission(request, None))
        self.assertFalse(IsTenantDesigner().has_permission(request, None))
