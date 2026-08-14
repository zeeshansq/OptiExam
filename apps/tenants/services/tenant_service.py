from typing import Optional, Dict
from django.db import transaction
from apps.tenants.models import Tenant, TenantFeatureFlag

@transaction.atomic
def create_tenant(
    name: str,
    slug: str,
    tier: str = Tenant.Tier.STARTER,
    domain: Optional[str] = None,
    primary_color: str = '#4F46E5',
    max_concurrent_candidates: int = 100,
    contact_email: Optional[str] = None,
    feature_overrides: Optional[Dict[str, bool]] = None
) -> Tenant:
    """
    Provisions a new educational institution / corporate tenant
    along with its baseline feature flags.
    """
    tenant = Tenant.objects.create(
        name=name,
        slug=slug,
        tier=tier,
        domain=domain,
        primary_color=primary_color,
        max_concurrent_candidates=max_concurrent_candidates,
        contact_email=contact_email,
        is_active=True
    )
    
    initialize_default_feature_flags(tenant, feature_overrides)
    return tenant

def initialize_default_feature_flags(tenant: Tenant, overrides: Optional[Dict[str, bool]] = None) -> None:
    """Initializes all standard TenantFeatureFlag entries for a tenant."""
    overrides = overrides or {}
    for feature_choice in TenantFeatureFlag.Feature.values:
        enabled_state = overrides.get(feature_choice, True)
        TenantFeatureFlag.objects.update_or_create(
            tenant=tenant,
            feature_key=feature_choice,
            defaults={'is_enabled': enabled_state}
        )

def toggle_feature_flag(tenant: Tenant, feature_key: str, is_enabled: Optional[bool] = None) -> TenantFeatureFlag:
    """Toggles or sets a specific feature flag for a tenant."""
    flag, created = TenantFeatureFlag.objects.get_or_create(
        tenant=tenant,
        feature_key=feature_key,
        defaults={'is_enabled': True}
    )
    if is_enabled is not None:
        flag.is_enabled = is_enabled
    else:
        # Toggle current state
        flag.is_enabled = not flag.is_enabled if not created else False
    flag.save()
    return flag
