import pytest
from django.test import RequestFactory
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole

@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        name="National Engineering College",
        slug="nec",
        tier=Tenant.Tier.PROFESSIONAL,
        is_active=True
    )

@pytest.fixture
def super_admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        email="admin@optiexam.local",
        password="AdminPass2026!",
        role=UserRole.SUPER_ADMIN
    )

@pytest.fixture
def designer_user(db, tenant):
    user = User.objects.create_user(
        username="designer",
        email="designer@nec.edu",
        password="DesignerPass2026!",
        tenant=tenant,
        role=UserRole.DESIGNER
    )
    return user

@pytest.fixture
def participant_user(db, tenant):
    user = User.objects.create_user(
        username="student",
        email="student@nec.edu",
        password="StudentPass2026!",
        tenant=tenant,
        role=UserRole.PARTICIPANT
    )
    return user

@pytest.fixture
def request_factory():
    return RequestFactory()
