from typing import Optional
from django.db import transaction
from apps.accounts.models import User, UserRole, UserProfile, AuditLog
from apps.accounts.services.auth_service import record_audit_log
from apps.tenants.models import Tenant

@transaction.atomic
def provision_user(
    username: str,
    email: str,
    password: str,
    role: str = UserRole.PARTICIPANT,
    tenant: Optional[Tenant] = None,
    first_name: str = '',
    last_name: str = '',
    phone_number: Optional[str] = None,
    registration_number: Optional[str] = None,
    department: Optional[str] = None,
    batch_year: Optional[str] = None,
    created_by: Optional[User] = None
) -> User:
    """
    Provisions a new User with attached UserProfile and records an audit log.
    """
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        tenant=tenant,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        is_verified=True
    )

    UserProfile.objects.create(
        user=user,
        registration_number=registration_number,
        department=department,
        batch_year=batch_year
    )

    record_audit_log(
        action=f"User '{username}' provisioned with role '{role}'",
        category=AuditLog.ActionCategory.ADMIN_OP,
        user=created_by,
        tenant=tenant,
        payload={'new_user_id': user.id, 'role': role, 'username': username}
    )

    return user
