from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from apps.tenants.models import Tenant

SYSTEM_PREFIXES = {
    'admin', 'auth', 'django-admin', 'static', 'media', 'api',
    'core', 'questions', 'exams', 'grading', 'analytics', 'submissions', 'healthz',
    'favicon.ico', '__debug__'
}

class TenantResolutionMiddleware(MiddlewareMixin):
    """
    Middleware that determines the active tenant for the incoming HTTP request.
    Attaches the resolved Tenant instance to `request.tenant`.
    """
    def process_request(self, request):
        tenant_slug = self._resolve_tenant_slug(request)
        
        if tenant_slug:
            try:
                request.tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            except Tenant.DoesNotExist:
                return HttpResponseForbidden("Institution not found or currently inactive.")
        elif getattr(request, 'user', None) and request.user.is_authenticated and getattr(request.user, 'tenant', None):
            request.tenant = request.user.tenant
        else:
            request.tenant = None

    def _resolve_tenant_slug(self, request):
        # 1. Inspect URL path prefix (e.g. /nec/dashboard/)
        path_parts = request.path.strip('/').split('/')
        if path_parts and len(path_parts) > 0 and path_parts[0]:
            first_part = path_parts[0]
            if first_part not in SYSTEM_PREFIXES:
                return first_part

        # 2. Check session or cookie safely
        session = getattr(request, 'session', {})
        cookies = getattr(request, 'COOKIES', {})
        return session.get('tenant_slug') or cookies.get('opti_tenant')
