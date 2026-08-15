from django.conf import settings
from django.core.cache import cache
from apps.accounts.models import UserRole

def tenant_context(request):
    """
    Injects current tenant identity, theme colors, and cached feature flags.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant and request.user.is_authenticated and hasattr(request.user, 'tenant'):
        tenant = request.user.tenant

    if not tenant:
        return {
            'current_tenant': None,
            'tenant_name': 'OptiExam Platform',
            'tenant_slug': None,
            'tenant_logo': None,
            'tenant_primary_color': '#4F46E5',
            'tenant_feature_flags': {},
        }

    cache_key = f'tenant_feature_flags_{tenant.pk}'
    feature_flags = cache.get(cache_key)
    if feature_flags is None:
        feature_flags = {
            flag.feature_key: flag.is_enabled
            for flag in tenant.feature_flags.all()
        }
        cache.set(cache_key, feature_flags, timeout=300)

    return {
        'current_tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_slug': tenant.slug,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'tenant_primary_color': tenant.primary_color,
        'tenant_feature_flags': feature_flags,
    }

def user_role_context(request):
    """
    Injects boolean flags and role display text for top-nav visibility.
    """
    user = request.user
    if not user.is_authenticated:
        return {
            'is_super_admin': False,
            'is_designer': False,
            'is_item_writer': False,
            'is_grader': False,
            'is_participant': False,
            'user_role_name': 'Guest',
            'user_avatar': None,
        }

    role = user.role
    return {
        'is_super_admin': user.is_super_admin(),
        'is_designer': user.is_designer(),
        'is_item_writer': user.is_item_writer(),
        'is_grader': user.is_grader(),
        'is_participant': user.is_participant(),
        'user_role_name': user.get_role_display(),
        'user_avatar': user.avatar.url if user.avatar else None,
    }

def notification_context(request):
    """
    Supplies the top-nav notification bell with unread alert counts.
    """
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    try:
        from apps.accounts.models import Notification
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_alerts = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    except Exception:
        unread_count = 0
        recent_alerts = []

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_alerts,
    }

def active_exam_context(request):
    """
    Displays persistent top banner enabling 1-click resume if candidate has active attempt.
    """
    if not request.user.is_authenticated or request.user.role != UserRole.PARTICIPANT:
        return {'active_exam_attempt': None}

    try:
        from submissions.models import ExamAttempt
        active_attempt = ExamAttempt.objects.filter(
            participant=request.user,
            status=ExamAttempt.Status.IN_PROGRESS
        ).select_related('exam').first()
    except (ImportError, Exception):
        active_attempt = None

    return {'active_exam_attempt': active_attempt}

def system_settings_context(request):
    """
    Injects platform version, offline status, and user dark mode preferences.
    """
    user_theme = 'dark'
    if request.user.is_authenticated:
        user_theme = request.session.get('ui_theme', 'dark')

    return {
        'OPTIEXAM_VERSION': getattr(settings, 'OPTIEXAM_VERSION', '1.0.0'),
        'IS_OFFLINE_READY': True,
        'SITE_TITLE': 'OptiExam',
        'ui_theme': user_theme,
        'is_dark_mode': user_theme == 'dark',
        'ENABLE_DEMO_LOGINS': getattr(settings, 'ENABLE_DEMO_LOGINS', True),
    }

