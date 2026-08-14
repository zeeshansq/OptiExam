from django.test import TestCase, RequestFactory
from django.views import View
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole
from apps.core.mixins import (
    SuperAdminRequiredMixin, DesignerRequiredMixin,
    ItemWriterRequiredMixin, GraderRequiredMixin, ParticipantRequiredMixin
)

class DummySuperAdminView(SuperAdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("SUCCESS")

class DummyDesignerView(DesignerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("DESIGNER_SUCCESS")

class DummyParticipantView(ParticipantRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("PARTICIPANT_SUCCESS")

class RBACMixinsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(name="Tech Institute", slug="tech-inst")

        self.super_admin = User.objects.create_superuser(username="sa", role=UserRole.SUPER_ADMIN)
        self.designer = User.objects.create_user(username="des", tenant=self.tenant, role=UserRole.DESIGNER)
        self.student = User.objects.create_user(username="stu", tenant=self.tenant, role=UserRole.PARTICIPANT)

    def test_super_admin_mixin_denies_non_super_admin(self):
        request = self.factory.get('/')
        request.user = self.designer
        view = DummySuperAdminView.as_view()
        with self.assertRaises(PermissionDenied):
            view(request)

    def test_super_admin_mixin_allows_super_admin(self):
        request = self.factory.get('/')
        request.user = self.super_admin
        view = DummySuperAdminView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "SUCCESS")

    def test_designer_mixin_allows_designer(self):
        request = self.factory.get('/')
        request.user = self.designer
        request.tenant = self.tenant
        view = DummyDesignerView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "DESIGNER_SUCCESS")

    def test_participant_mixin_allows_student(self):
        request = self.factory.get('/')
        request.user = self.student
        request.tenant = self.tenant
        view = DummyParticipantView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "PARTICIPANT_SUCCESS")

class ZeroCDNOfflineTest(TestCase):
    def test_rendered_base_template_has_zero_external_cdn_links(self):
        """Verifies templates contain 0 external CDN links (http/https) in script or link tags."""
        rendered_html = render_to_string('base.html', {'ui_theme': 'dark'})
        
        forbidden_cdns = [
            'fonts.googleapis.com',
            'cdnjs.cloudflare.com',
            'cdn.jsdelivr.net',
            'unpkg.com',
            'http://',
            'https://'
        ]
        
        for cdn in forbidden_cdns:
            self.assertNotIn(
                cdn,
                rendered_html,
                f"Forbidden external link or CDN '{cdn}' detected in base.html!"
            )
