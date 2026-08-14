from django.contrib import admin
from apps.tenants.models import Tenant, TenantFeatureFlag

class TenantFeatureFlagInline(admin.TabularInline):
    model = TenantFeatureFlag
    extra = 1

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'tier', 'is_active', 'max_concurrent_candidates', 'created_at')
    list_filter = ('tier', 'is_active')
    search_fields = ('name', 'slug', 'domain')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TenantFeatureFlagInline]

@admin.register(TenantFeatureFlag)
class TenantFeatureFlagAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'feature_key', 'is_enabled', 'updated_at')
    list_filter = ('feature_key', 'is_enabled')
