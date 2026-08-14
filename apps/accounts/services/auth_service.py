from typing import Optional, Dict, Any
from django.urls import reverse
from apps.accounts.models import User, UserRole, AuditLog
from apps.tenants.models import Tenant

def record_audit_log(
    action: str,
    category: str = AuditLog.ActionCategory.AUTH,
    user: Optional[User] = None,
    tenant: Optional[Tenant] = None,
    request = None,
    payload: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Persists a security or operational event to the AuditLog table.
    """
    ip_address = None
    user_agent = None

    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        if not tenant and getattr(request, 'tenant', None):
            tenant = request.tenant
        if not user and request.user.is_authenticated:
            user = request.user

    return AuditLog.objects.create(
        tenant=tenant,
        user=user,
        category=category,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        payload=payload or {}
    )

def get_redirect_url_for_user(user: User) -> str:
    """
    Resolves the post-login destination URL dynamically based on user role.
    """
    if user.is_super_admin():
        return reverse('tenants:super_admin_dashboard')

    tenant_slug = user.tenant.slug if user.tenant else 'default'

    if user.is_designer():
        return reverse('tenants:designer_dashboard', kwargs={'tenant_slug': tenant_slug})
    elif user.is_item_writer():
        return reverse('tenants:item_writer_dashboard', kwargs={'tenant_slug': tenant_slug})
    elif user.is_grader():
        return reverse('tenants:grader_dashboard', kwargs={'tenant_slug': tenant_slug})
    else:  # PARTICIPANT
        return reverse('tenants:participant_dashboard', kwargs={'tenant_slug': tenant_slug})

