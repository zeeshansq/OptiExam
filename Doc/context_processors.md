# Template Context Processors Specification — OptiExam Global UI State
**Document Version:** 1.0.0  
**Project:** OptiExam Assessment Platform  
**Document Purpose:** Defines all global context processors injected into Django templates automatically, eliminating boilerplate view context variables across the application.

---

## 1. Overview & Architecture

To keep Django Class-Based Views thin and consistent, global UI state (institutional branding, top-nav notifications, user role flags, active exam resume banners, and offline status) is injected globally via **5 specialized Context Processors** located in `apps/core/context_processors.py`.

```
                        HTTP Request
                             │
                             ▼
              ┌─────────────────────────────┐
              │  Django View (Thin Context) │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │  Core Context Processors    │
              │  - Tenant & Branding        │
              │  - User Role Flags          │
              │  - In-App Notifications     │
              │  - Active Exam Banner       │
              │  - System Offline Status    │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │  Master Template Rendering  │
              │  (base_app.html / Top-Nav)  │
              └─────────────────────────────┘
```

---

## 2. Context Processors Catalog

### 2.1 `tenant_context(request)`
Injects the active institution's profile, custom logo, theme colors, and active feature flags.

```python
# apps/core/context_processors.py
from tenants.models import Tenant

def tenant_context(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant and request.user.is_authenticated and hasattr(request.user, 'tenant'):
        tenant = request.user.tenant

    if not tenant:
        return {
            'current_tenant': None,
            'tenant_name': 'OptiExam Platform',
            'tenant_logo': None,
            'tenant_primary_color': '#4F46E5',
            'tenant_feature_flags': {},
        }

    # Cache feature flags in a fast dictionary
    feature_flags = {
        flag.feature_key: flag.is_enabled 
        for flag in tenant.feature_flags.all()
    }

    return {
        'current_tenant': tenant,
        'tenant_name': tenant.name,
        'tenant_slug': tenant.slug,
        'tenant_logo': tenant.logo.url if tenant.logo else None,
        'tenant_primary_color': tenant.primary_color,
        'tenant_feature_flags': feature_flags,
    }
```

---

### 2.2 `user_role_context(request)`
Injects boolean flags and role metadata for top-nav item visibility and template authorization.

```python
# apps/core/context_processors.py
from accounts.models import UserRole

def user_role_context(request):
    user = request.user
    if not user.is_authenticated:
        return {
            'is_super_admin': False,
            'is_designer': False,
            'is_item_writer': False,
            'is_grader': False,
            'is_participant': False,
            'user_role_name': 'Guest',
        }

    role = user.role
    return {
        'is_super_admin': role == UserRole.SUPER_ADMIN or user.is_superuser,
        'is_designer': role == UserRole.DESIGNER,
        'is_item_writer': role == UserRole.ITEM_WRITER,
        'is_grader': role == UserRole.GRADER,
        'is_participant': role == UserRole.PARTICIPANT,
        'user_role_name': user.get_role_display(),
        'user_avatar': user.avatar.url if user.avatar else None,
    }
```

---

### 2.3 `notification_context(request)`
Supplies the top-nav notification bell with the unread count and the latest 5 unread alerts.

```python
# apps/core/context_processors.py
from notifications.models import Notification

def notification_context(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False)
    unread_count = unread_qs.count()
    recent_alerts = unread_qs.order_by('-created_at')[:5]

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_alerts,
    }
```

---

### 2.4 `active_exam_context(request)`
If an authenticated participant has an exam in progress, displays a persistent top banner enabling instant 1-click resume.

```python
# apps/core/context_processors.py
from submissions.models import ExamAttempt

def active_exam_context(request):
    if not request.user.is_authenticated or request.user.role != 'PARTICIPANT':
        return {'active_exam_attempt': None}

    active_attempt = ExamAttempt.objects.filter(
        participant=request.user,
        status=ExamAttempt.Status.IN_PROGRESS
    ).select_related('exam').first()

    return {
        'active_exam_attempt': active_attempt
    }
```

---

### 2.5 `system_settings_context(request)`
Injects platform version, offline asset status, and dark mode preferences.

```python
# apps/core/context_processors.py
from django.conf import settings

def system_settings_context(request):
    return {
        'OPTIEXAM_VERSION': getattr(settings, 'OPTIEXAM_VERSION', '1.0.0'),
        'IS_OFFLINE_READY': True,
        'SITE_TITLE': 'OptiExam',
    }
```

---

## 3. Registration in `optiexam/settings/base.py`

```python
# optiexam/settings/base.py

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Custom OptiExam Universal Context Processors
                'apps.core.context_processors.tenant_context',
                'apps.core.context_processors.user_role_context',
                'apps.core.context_processors.notification_context',
                'apps.core.context_processors.active_exam_context',
                'apps.core.context_processors.system_settings_context',
            ],
        },
    },
]
```

---

## 4. Master Template Usage Examples

### 4.1 Top Navigation Bar (`templates/includes/top_nav.html`)
```html
<header class="top-nav" style="border-top: 3px solid {{ tenant_primary_color }};">
  <div class="nav-brand">
    {% if tenant_logo %}
      <img src="{{ tenant_logo }}" alt="{{ tenant_name }}" class="brand-logo">
    {% endif %}
    <span class="brand-title">{{ tenant_name }}</span>
  </div>

  <!-- Active Exam Resume Banner if Candidate has session in progress -->
  {% if active_exam_attempt %}
    <div class="active-exam-alert-pill">
      <span class="pulse-dot"></span>
      <span>Live Exam: {{ active_exam_attempt.exam.title }}</span>
      <a href="{% url 'submissions:cockpit' active_exam_attempt.id %}" class="btn-resume">Resume Exam</a>
    </div>
  {% endif %}

  <div class="nav-actions">
    <!-- Fullscreen Toggle Icon -->
    <button id="btn-fullscreen-toggle" class="nav-icon-btn" title="Toggle Fullscreen" aria-label="Toggle Fullscreen">
      <svg class="icon"><use href="{% static 'icons/lucide-sprite.svg#maximize' %}"></use></svg>
    </button>

    <!-- In-App Notification Bell -->
    <div class="dropdown notification-dropdown">
      <button class="nav-icon-btn" id="notification-bell">
        <svg class="icon"><use href="{% static 'icons/lucide-sprite.svg#bell' %}"></use></svg>
        {% if unread_notifications_count > 0 %}
          <span class="badge-count">{{ unread_notifications_count }}</span>
        {% endif %}
      </button>
      <div class="dropdown-menu notification-menu">
        <h4>Notifications</h4>
        {% for note in recent_notifications %}
          <div class="notification-item">
            <strong>{{ note.title }}</strong>
            <p>{{ note.message }}</p>
          </div>
        {% empty %}
          <p class="empty-text">No unread notifications</p>
        {% endfor %}
      </div>
    </div>

    <!-- User Profile Dropdown -->
    <div class="user-profile-badge">
      <span class="user-role-tag">{{ user_role_name }}</span>
      <span class="user-name">{{ request.user.get_full_name|default:request.user.username }}</span>
    </div>
  </div>
</header>
```
