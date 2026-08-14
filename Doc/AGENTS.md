# AGENTS.md — AI Agent Directives & Repository Handbook
**Project:** OptiExam Assessment Platform  
**Document Version:** 2.0.0  
**Target Engine:** Django 5.x / Python 3.12+  
**Audit:** 2026-08-14 — Added: Testing protocols, Migration commands, Linting setup, Middleware architecture, Signals, URL namespacing.

---

## 1. AI Agent Persona & Core Directive

You are the **Principal Software Architect & Lead Django Engineer** for **OptiExam**. Every code file, template, style rule, and test you write must adhere to enterprise SaaS standards: robust, decoupled, secure, 100% offline-ready, and multi-tenant safe.

---

## 2. The 10 Invariant Architectural Commandments

### 1. Strict Multi-Tenant Data Isolation
* **Rule:** Never query a tenant-scoped model without filtering by tenant.
* **Bad:**  `Exam.objects.filter(id=exam_id)`
* **Good:** `Exam.objects.for_tenant(request.tenant).filter(id=exam_id)`

### 2. 100% Offline-First Asset Rule (Zero CDN Rule)
* **Rule:** NEVER include external CDN links in templates.
* **Forbidden:** `https://fonts.googleapis.com`, `https://cdnjs...`, `https://cdn.jsdelivr...`
* **Required:** All assets via `{% static 'path/to/asset' %}` pointing to local `/static/`.

### 3. Server-Authoritative Examination Time
* **Rule:** Never trust client timestamps or client-reported remaining time.
* **Formula:**
  ```
  deadline = attempt.started_at + exam.duration_minutes + attempt.bonus_minutes_awarded
  remaining = deadline - timezone.now()
  ```
  This is computed on the server on every heartbeat response. The client only uses it for display.

### 4. Service Layer & Selector Pattern (No Fat Views)
* **Rule:** Views are controllers only. All business logic → `services/`. All complex reads → `selectors/`.
* **Permitted in views:** Form validation, permission checks, calling services, calling selectors, returning HTTP response.
* **Forbidden in views:** Raw ORM mutations, multi-model transactions, sending emails/notifications.

### 5. Custom User Model Access
* **NEVER:** `from django.contrib.auth.models import User`
* **ALWAYS:** `from django.contrib.auth import get_user_model; User = get_user_model()`

### 6. Migration-Safe Model Defaults
* **NEVER:** `default={}` or `default=[]` (mutable defaults cause migration bugs)
* **ALWAYS:** `default=dict` or `default=list`
* Never use bare `datetime.now` — use `django.utils.timezone.now` (callable)

### 7. Database Transaction Atomicity
* **Rule:** Any service function that writes to multiple tables MUST use `@transaction.atomic`.
* **Required for:** Exam start, answer submission, bonus time grants, grader finalization, result publication.

### 8. Anti-Cheating & Proctoring Event Safety
* **Rule:** Proctoring log writes must never block or crash the candidate's exam session.
* **Pattern:** Wrap `ProctoringLog.objects.create(...)` in a `try/except` block; silently log failures via Python `logging` module.

### 9. 5-Tier Role-Based Security Enforcement
Every CBV must inherit one of these RBAC mixins from `apps/core/mixins.py`:
```python
SuperAdminRequiredMixin   # SUPER_ADMIN only
DesignerRequiredMixin     # DESIGNER only
ItemWriterRequiredMixin   # ITEM_WRITER or DESIGNER
GraderRequiredMixin       # GRADER only
ParticipantRequiredMixin  # PARTICIPANT only
TenantStaffRequiredMixin  # Any of DESIGNER, ITEM_WRITER, GRADER
```

### 10. Clean, Modern, Accessible UI Design
* Follow the OptiExam Design System CSS variables (see `Doc/PRD.md` Section 3.3).
* All pages must have comprehensive guide text and colorful Lucide icons on configuration options.
* All interactive elements must have `id` attributes, `aria-label`, and `tabindex` where appropriate.

---

## 3. Environment & Execution Guidelines

### 3.1 Virtual Environment (Windows PowerShell)
```powershell
# Activate environment
& "C:\venv\envoptiexam\Scripts\Activate.ps1"

# Run management commands
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
python manage.py collectstatic --noinput

# Run tests with coverage
python -m pytest --cov=apps --cov-report=term-missing -v
```

### 3.2 Linting & Code Quality
OptiExam uses `ruff` and `black` for consistent formatting:
```powershell
# Format code
black apps/ --line-length 100

# Lint and auto-fix
ruff check apps/ --fix

# Type checking
mypy apps/ --ignore-missing-imports
```

### 3.3 Django Migration Workflow
```powershell
# Create migrations after model changes
python manage.py makemigrations <app_name>

# Show pending migrations
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Squash migrations (after stable releases)
python manage.py squashmigrations <app_name> 0001 0020
```

### 3.4 Dual Database Strategy
| Environment | Engine | Connection |
|---|---|---|
| Development / Offline | SQLite | `sqlite:///db.sqlite3` |
| Production SaaS | PostgreSQL 16+ | `DATABASE_URL` env variable |

Database switching is controlled entirely through `.env` settings. Code must not hard-code engine-specific SQL.

---

## 4. Multi-Tenant Middleware Architecture

### 4.1 `TenantResolutionMiddleware`
Location: `apps/core/middleware.py`

Resolves the active tenant on every request and attaches it to `request.tenant`:

```python
# apps/core/middleware.py
from django.http import HttpResponseForbidden
from tenants.models import Tenant

class TenantResolutionMiddleware:
    """
    Resolves request.tenant from:
    1. URL path slug (/{tenant_slug}/...)
    2. Custom domain header
    3. Session cookie (TENANT_COOKIE_NAME)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Resolution logic: URL slug → Domain → Cookie → None (SaaS admin routes)
        tenant_slug = self._resolve_slug(request)
        if tenant_slug:
            try:
                request.tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            except Tenant.DoesNotExist:
                return HttpResponseForbidden("Institution not found or inactive.")
        else:
            request.tenant = None  # Super Admin routes have no tenant
        return self.get_response(request)

    def _resolve_slug(self, request):
        # 1. Check URL prefix
        path_parts = request.path.strip('/').split('/')
        if path_parts and len(path_parts) > 0:
            candidate = path_parts[0]
            if Tenant.objects.filter(slug=candidate, is_active=True).exists():
                return candidate
        # 2. Check session
        return request.session.get('tenant_slug')
```

### 4.2 Middleware Order in `settings/base.py`
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.TenantResolutionMiddleware',  # ← AFTER auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

---

## 5. URL Namespace Conventions

Every app MUST define a `app_name` in its `urls.py`:

```python
# apps/exams/urls.py
app_name = 'exams'

urlpatterns = [
    path('', views.ExamListView.as_view(), name='list'),
    path('create/', views.ExamCreateView.as_view(), name='create'),
    path('<int:pk>/live/', views.LiveOpsView.as_view(), name='live_ops'),
]
```

Usage in templates: `{% url 'exams:list' %}`, `{% url 'submissions:cockpit' attempt.id %}`

| App | Namespace | Base URL Prefix |
|---|---|---|
| `accounts` | `accounts` | `/auth/` |
| `tenants` | `tenants` | `/admin/tenants/` |
| `exams` | `exams` | `/{tenant}/exams/` |
| `questions` | `questions` | `/{tenant}/questions/` |
| `submissions` | `submissions` | `/{tenant}/exam/` |
| `grading` | `grading` | `/{tenant}/grading/` |
| `notifications` | `notifications` | `/{tenant}/notifications/` |

---

## 6. Signal Architecture (`apps/<app>/signals.py`)

Use Django signals sparingly, only for cross-app side-effects:

```python
# apps/submissions/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from submissions.models import ExamAttempt
from notifications.services.notification_service import dispatch_notification

@receiver(post_save, sender=ExamAttempt)
def notify_on_submission(sender, instance, **kwargs):
    """Send notification to Designer when a participant submits."""
    if instance.status == ExamAttempt.Status.SUBMITTED:
        # Notify designer (non-blocking, fire-and-forget)
        pass
```

---

## 7. Testing Protocols

### 7.1 Required Test Coverage
| Component | Minimum Coverage |
|---|---|
| Service functions (all) | 95% |
| Selectors (all) | 90% |
| Views (RBAC checks) | 100% |
| Model validators | 90% |
| API endpoints | 85% |

### 7.2 Required Test Types
```python
# Tenant isolation test (MANDATORY for every new model)
class TestTenantIsolation(TestCase):
    def test_tenant_a_cannot_see_tenant_b_exams(self):
        tenant_a = Tenant.objects.create(name='A', slug='a')
        tenant_b = Tenant.objects.create(name='B', slug='b')
        exam_b = Exam.objects.create(tenant=tenant_b, ...)
        
        # Querying tenant A's scope must return zero results
        results = Exam.objects.for_tenant(tenant_a).filter(pk=exam_b.pk)
        self.assertEqual(results.count(), 0)

# Role-based access test (MANDATORY for every view)
class TestDesignerAccessControl(TestCase):
    def test_participant_cannot_access_live_ops(self):
        response = self.client.get('/nec/exams/1/live/')
        self.assertEqual(response.status_code, 403)
```

### 7.3 Pytest Configuration (`conftest.py`)
```python
# conftest.py (project root)
import pytest
from django.test import RequestFactory
from tenants.models import Tenant

@pytest.fixture
def tenant():
    return Tenant.objects.create(name='Test Institution', slug='test-inst')

@pytest.fixture
def request_factory():
    return RequestFactory()
```

---

## 7. Whole-Project UI/UX & Architectural Invariants

Whenever an AI agent implements any view, form, or template across Phase 1 to Phase 5:
1. **100% Full-Screen Width Layout:** Always use `.container` or `.container-fluid` (`width: 100%; max-width: 100%;`). Never introduce narrow boxed layout containers.
2. **Single-Line Filter Toolbar:** Filter bars on tabular pages must fit search, dropdowns, submit button, and clear button (`rotate-ccw`) in a single line (`.filter-row-single`).
3. **Interactive Sorting & Windowed Pagination:** All list queries must be paginated with `{% include "includes/pagination.html" %}` and table column headers must use `{% sort_header 'field' 'Label' %}`.
4. **Categorized Smart Forms:** Multi-field forms must use `.form-section-card` groupings with sensible prefilled defaults and smart helpers.
5. **Zero CDN Compliance:** 100% offline static assets (local SVG sprite via `{% icon 'name' %}`).

