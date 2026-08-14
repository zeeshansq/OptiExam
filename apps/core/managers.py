from django.db import models

class TenantQuerySet(models.QuerySet):
    """
    Custom QuerySet providing tenant-scoped query filters.
    """
    def for_tenant(self, tenant):
        if tenant is None:
            return self.none()
        return self.filter(tenant=tenant)

class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    """
    Custom Manager providing tenant isolation methods across models.
    """
    pass
