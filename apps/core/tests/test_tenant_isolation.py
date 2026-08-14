from django.test import TestCase
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole
from apps.core.models import DataImportJob

class TenantIsolationTest(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant Alpha", slug="alpha")
        self.tenant_b = Tenant.objects.create(name="Tenant Beta", slug="beta")

        self.user_a = User.objects.create_user(
            username="user_a",
            password="pass",
            tenant=self.tenant_a,
            role=UserRole.DESIGNER
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            password="pass",
            tenant=self.tenant_b,
            role=UserRole.DESIGNER
        )

        # Create tenant-scoped import job
        self.job_a = DataImportJob.objects.create(
            tenant=self.tenant_a,
            import_type=DataImportJob.ImportType.PARTICIPANT_ROSTER,
            created_by=self.user_a,
            total_rows=10
        )
        self.job_b = DataImportJob.objects.create(
            tenant=self.tenant_b,
            import_type=DataImportJob.ImportType.PARTICIPANT_ROSTER,
            created_by=self.user_b,
            total_rows=20
        )

    def test_for_tenant_scoping(self):
        """Verify for_tenant manager method isolates records strictly per tenant."""
        jobs_a = DataImportJob.objects.for_tenant(self.tenant_a)
        self.assertEqual(jobs_a.count(), 1)
        self.assertEqual(jobs_a.first().id, self.job_a.id)

        jobs_b = DataImportJob.objects.for_tenant(self.tenant_b)
        self.assertEqual(jobs_b.count(), 1)
        self.assertEqual(jobs_b.first().id, self.job_b.id)

    def test_null_tenant_scoping_returns_none(self):
        """Verify for_tenant(None) returns empty queryset."""
        jobs_none = DataImportJob.objects.for_tenant(None)
        self.assertEqual(jobs_none.count(), 0)
