from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import User, UserProfile, AuditLog

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'tenant', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'tenant')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('OptiExam Multi-Tenancy & Roles', {'fields': ('tenant', 'role', 'phone_number', 'avatar', 'is_verified')}),
    )
    inlines = [UserProfileInline]

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'category', 'user', 'tenant', 'ip_address', 'timestamp')
    list_filter = ('category', 'tenant')
    search_fields = ('action', 'ip_address', 'user__username')
    readonly_fields = ('timestamp',)
