# Project Rules & Development Standards — OptiExam
**Document Version:** 2.0.0  
**Audit:** 2026-08-14 — Added: URL naming, template naming, logging standards, requirements policy, middleware rules, management commands.

---

## 1. Code Standards & Python Conventions

### 1.1 Python 3.12+ & Django 5.x Standards
1. **Type Annotations:** All service functions, selectors, model methods, and helper utilities must be fully type-hinted.
   ```python
   from django.db import models
   from submissions.models import ExamAttempt

   def award_bonus_time(attempt_id: int, bonus_minutes: int, reason: str) -> ExamAttempt:
       ...
   ```
2. **Explicit Imports:** No wildcard imports. Import ordering: stdlib → third-party → Django → internal apps.
3. **Docstrings:** Google-style docstrings on all public service functions, selectors, and complex model methods.
4. **Linting tools:**
   * `black .` — Code formatter (line length 100)
   * `ruff check . --fix` — Linter with auto-fix
   * `mypy apps/` — Type checker
5. **Line Length:** Maximum 100 characters.
6. **String Formatting:** f-strings for all string interpolation.

---

## 2. Multi-Tenancy & Query Isolation Rules

### 2.1 The `TenantModelMixin` Pattern
Every model that stores tenant data must inherit from `TenantModelMixin` (defined in `apps/core/models.py`):

```python
class MyTenantModel(TenantModelMixin, models.Model):
    name = models.CharField(max_length=100)
    # TenantModelMixin adds: tenant FK + TenantManager (for_tenant)
```

### 2.2 Tenant Query Rules
* **ALWAYS** scope tenant queries: `Model.objects.for_tenant(request.tenant).filter(...)`
* **NEVER** use global unscoped queries on tenant-bound models in views, services, or selectors.
* **API endpoints** must validate `obj.tenant == request.tenant` before returning any object.

### 2.3 Tenant Resolution
* Tenant is attached to `request.tenant` by `TenantResolutionMiddleware`.
* `request.tenant` is `None` only for Super Admin routes (e.g., `/admin/saas/`).
* In services, pass `tenant` explicitly, never access `request` inside service functions.

---

## 3. 100% Offline Asset & Styling Rules

### 3.1 Zero External Request Policy (ABSOLUTE)
* **FORBIDDEN in any template:**
  ```html
  <link href="https://fonts.googleapis.com/...">
  <script src="https://cdn.jsdelivr.net/..."></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/...">
  ```
* **REQUIRED:**
  ```html
  <link rel="stylesheet" href="{% static 'css/optiexam-core.css' %}">
  <script src="{% static 'js/optiexam-core.js' %}"></script>
  ```

### 3.2 Local Font Declaration
All fonts declared in `optiexam-core.css` using local `@font-face`:
```css
@font-face {
  font-family: 'Inter';
  font-weight: 400;
  font-display: swap;
  src: url("{% static 'fonts/inter/Inter-Regular.woff2' %}") format('woff2');
}
```

### 3.3 Icon Usage
Use inline SVG `<use>` with local sprite only:
```html
<svg class="icon" aria-hidden="true">
  <use href="{% static 'icons/lucide-sprite.svg#bell' %}"></use>
</svg>
```

---

## 4. Anti-Cheating & Proctoring Integrity Rules

1. **Server-Authoritative Clock:** Remaining time computed server-side. Client clock is cosmetic only.
2. **Non-Blocking Proctoring Logs:** `ProctoringLog.objects.create(...)` must be in `try/except` to never crash an active exam session.
3. **Heartbeat Safety:** If heartbeat API fails, client queues to `localStorage` and retries with exponential backoff (3s, 6s, 12s).
4. **Violation Escalation:** Violation count tracked on `ExamAttempt.violation_count`. Reaching `exam.max_tab_violations` triggers auto-submission via `submission_service.auto_submit_attempt(attempt)`.

---

## 5. Security & Access Control Rules

### 5.1 Role Constants
Always reference `UserRole` enum:
```python
from accounts.models import UserRole
if user.role == UserRole.DESIGNER: ...
```

### 5.2 View Permission Mixins (in `apps/core/mixins.py`)
```python
class SuperAdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_super_admin():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
```

### 5.3 API Permission Classes (`apps/core/permissions.py`)
DRF-compatible permission classes for API views:
```python
class IsTenantDesigner(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                request.user.role == UserRole.DESIGNER and
                request.user.tenant == request.tenant)
```

---

## 6. URL Namespace & Routing Rules

1. **Every app MUST declare `app_name`** in its `urls.py`.
2. **URL names must be lowercase, hyphen-separated** (not underscores): e.g., `exam-create`, `exam-list`, `live-ops`.
3. **Always use `reverse()` / `{% url %}` with namespace**: `{% url 'exams:exam-list' %}`.
4. **Root URL patterns** (`optiexam/urls.py`) must use `include()` with namespace parameter:
   ```python
   path('<slug:tenant_slug>/exams/', include('apps.exams.urls', namespace='exams')),
   ```

---

## 7. Template Naming Conventions

| Pattern | Usage |
|---|---|
| `<app>/<model>_list.html` | List views |
| `<app>/<model>_detail.html` | Detail views |
| `<app>/<model>_form.html` | Create/Update forms |
| `<app>/<model>_confirm_delete.html` | Delete confirmation |
| `<app>/dashboard.html` | Role dashboard pages |
| `includes/<partial>.html` | Reusable partial templates |
| `base.html` | Root skeleton |
| `base_app.html` | App shell with top-nav |
| `base_exam_cockpit.html` | Exam lockdown screen |

---

## 8. Logging Standards

All apps must use Python's `logging` module, never `print()`:

```python
import logging
logger = logging.getLogger(__name__)

# Usage patterns
logger.debug("Heartbeat received for attempt %d", attempt_id)
logger.info("Exam %s started by user %d", exam.code, user.pk)
logger.warning("Proctoring violation for attempt %d: %s", attempt_id, violation_type)
logger.error("Failed to create proctoring log: %s", exc, exc_info=True)
```

Logging configuration in `settings/base.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{levelname}] {asctime} {module}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs/optiexam.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO'},
    'loggers': {
        'apps': {'level': 'DEBUG', 'handlers': ['console', 'file'], 'propagate': False},
    },
}
```

---

## 9. Database Transaction & Data Integrity Rules

1. **Atomic Operations** — wrap with `@transaction.atomic` or `transaction.atomic()` context manager:
   * Exam start initialization
   * Exam submission & auto-scoring trigger
   * Grader batch assignment
   * Result publication
   * Bonus time grant (all attempts)
2. **Optimistic Locking** — `QuestionScore.version` field must be checked and incremented on every update.
3. **PROTECT on Critical Links** — Never use `CASCADE` where deletion would cause irreversible data loss:
   * `Exam → ExamAttempt`: use `PROTECT`
   * `Question → AttemptAnswer`: use `PROTECT`

---

## 10. Requirements & Package Management Rules

1. All packages must be pinned to exact versions in `requirements.txt`.
2. Separate `requirements-dev.txt` for development-only packages.
3. **Never** install packages with `--no-deps`; always resolve full dependency tree.
4. Required packages (see `Doc/project_layout.md` Section 3 for full list):
   * `Django>=5.0,<6.0`
   * `django-environ>=0.11`
   * `Pillow>=10.0` (image uploads)
   * `psycopg2-binary>=2.9` (PostgreSQL)
   * `pytest-django>=4.8`
   * `ruff>=0.4` (linting)
   * `black>=24.0` (formatting)

---

## 11. Management Commands

Custom Django management commands must be placed in `apps/<app>/management/commands/`:

```python
# apps/submissions/management/commands/auto_submit_expired.py
from django.core.management.base import BaseCommand
from submissions.services.submission_service import auto_submit_expired_attempts

class Command(BaseCommand):
    help = 'Auto-submit all expired exam attempts that are still IN_PROGRESS'

    def handle(self, *args, **options):
        count = auto_submit_expired_attempts()
        self.stdout.write(self.style.SUCCESS(f'Auto-submitted {count} expired attempts.'))
```

Run via: `python manage.py auto_submit_expired`

---

## 12. Bulk Data Ingestion & Import Integrity Rules

1. **Two-Stage Ingestion Invariant:** Never insert or mutate database records directly from an unvalidated uploaded file.
   * **Stage 1 (Dry-Run):** Parse and validate headers, foreign keys, and field types without writing to domain tables.
   * **Stage 2 (Commit):** Only when the user reviews the 10-row confirmation preview and clicks "Commit Import" does atomic ingestion execute.
2. **Downloadable Sample Templates:** Every import UI must provide 1-click download links to sample `.csv` and `.xlsx` templates containing valid example rows and inline column guidance.
3. **Atomic Batch Commits:** Bulk imports must execute within `with transaction.atomic():` to ensure an unexpected failure on row 450 rolls back the entire batch cleanly.
4. **Audit & Error Logging:** Every import job must record a `DataImportJob` entry storing metrics (total rows, processed, failed) and a line-by-line JSON error log.

---

## 13. Whole-Project Architectural & UI/UX Invariants (Mandatory Across All 5 Phases)

1. **100% Full-Screen Width Fluid Layout Invariant:**
   * Never constrain application views to fixed narrow containers (e.g. `1280px`).
   * All `.container` and `.container-fluid` classes MUST span `width: 100%; max-width: 100%;` with responsive `28px` gutter padding.
   * All tables, dashboards, Question Banks, Exam Cockpits, Live Ops matrices, and Split-Screen grading studios MUST fluidly utilize the full horizontal viewport real estate.

2. **Single-Line Filter Toolbar & Icon Clear Invariant:**
   * Every filter toolbar on any tabular data page MUST fit entirely in a **single horizontal line** using `.filter-row-single`.
   * Search input (`.filter-search-field`), dropdown filters (`.filter-dropdown-field`), the primary **Filter** submit button, and the **Clear/Reset** icon button (`rotate-ccw`) MUST sit side-by-side on the same row with consistent `38px` component heights.
   * When active filters exist, display **Active Filter Chips** above the table with 1-click `×` removal.

3. **Full-Featured Windowed Pagination & Clickable Column Sorting Invariant:**
   * Never render an unpaginated query for lists (Tenants, Users, Questions, Blueprints, Attempts, Grading Batches, Audit Logs).
   * Always paginate via Django (`paginate_by = 10|25|50|100`) and include `{% include "includes/pagination.html" %}`.
   * Column headers must support two-way ascending/descending sorting via `{% sort_header 'field' 'Label' %}` (`?sort=field&order=asc|desc`), preserving all active search query parameters across pagination.

4. **Categorized Smart Form & Helper Standard:**
   * Multi-field forms must be partitioned into **categorized card sections** (`.form-section-card`) with header icons, subtitles, and contextual guide boxes.
   * Supply sensible prefilled defaults for required fields (e.g. default quotas, default brand colors `#4F46E5`).
   * Provide interactive helper UI elements: 1-click color preset swatches, auto-slugification listeners, character counters, and password show/hide toggles.
   * Destructive actions (Deactivation, Deletion) must always require explicit confirmation via a dedicated modal or confirmation view.


