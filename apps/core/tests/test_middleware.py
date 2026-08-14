from django.test import TestCase, RequestFactory
from apps.tenants.models import Tenant
from apps.core.middleware import TenantResolutionMiddleware

class MiddlewareTenantResolutionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = Tenant.objects.create(name="Engineering College", slug="eng-col", is_active=True)
        self.middleware = TenantResolutionMiddleware(lambda req: None)

    def test_url_path_slug_resolution(self):
        request = self.factory.get('/eng-col/dashboard/')
        self.middleware.process_request(request)
        self.assertIsNotNone(request.tenant)
        self.assertEqual(request.tenant.slug, "eng-col")

    def test_unknown_slug_returns_403_forbidden(self):
        request = self.factory.get('/non-existent-institution/dashboard/')
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)
