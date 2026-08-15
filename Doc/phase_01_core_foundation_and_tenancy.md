# Phase 1: Core Foundation, Multi-Tenancy & Authentication Engine
**Document:** `Doc/phase_01_core_foundation_and_tenancy.md`  
**Project:** OptiExam Assessment Platform  
**Target Environment:** Python 3.12+ / Django 5.x / `C:\venv\envoptiexam`  
**Document Version:** 2.0.0  
**Phase Status:** COMPLETED & VERIFIED (33/33 Tests Passing)  

---

## 1. Phase Overview & Strategic Objectives

Phase 1 establishes the rock-solid architectural foundation of OptiExam. It delivers the multi-tenant runtime, modular configuration with dual-database support, local offline-ready design system (zero external CDN calls), the custom 5-tier user authentication engine, global template context processors, and the SaaS Super Admin provisioning hub.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PHASE 1 DELIVERABLES                          │
├────────────────────────────────────────────────────────────────────────┤
│  1. Django 5.x Project Initialization & Modular Settings Architecture  │
│  2. Dual Database Strategy (SQLite Dev/Offline + PostgreSQL Prod SaaS)  │
│  3. 100% Offline Static Design System (Inter, Outfit, Lucide SVGs)     │
│  4. Core Mixins & TenantResolutionMiddleware                           │
│  5. Custom User Model (`accounts.User`) with 5 User Roles              │
│  6. Tenant & TenantFeatureFlag Domain Models                           │
│  7. Universal Sleek Login View & Role-Based Post-Login Routing         │
│  8. Super Admin Tenant Provisioning Dashboard                          │
│  9. 5 Global Template Context Processors with Caching Strategy         │
│  10. Automated Test Suite for Multi-Tenant Isolation & Role Security   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Target Component & Directory Layout

During Phase 1, the following file and directory structure will be established:

```
c:\py-projects\OptiExam\
├── .env.example
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── conftest.py
├── pytest.ini
├── pyproject.toml
├── logs/
│   └── optiexam.log
├── optiexam/
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── local.py
│       └── production.py
├── apps/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py              # TenantModelMixin
│   │   ├── managers.py            # TenantQuerySet & TenantManager
│   │   ├── middleware.py          # TenantResolutionMiddleware
│   │   ├── mixins.py              # RBAC View Mixins (5 roles)
│   │   ├── permissions.py         # DRF Permission classes
│   │   ├── context_processors.py  # 5 global context processors with caching
│   │   ├── templatetags/
│   │   │   ├── __init__.py
│   │   │   ├── optiexam_tags.py
│   │   │   └── icon_tags.py
│   │   ├── utils.py
│   │   └── tests/
│   ├── tenants/
│   │   ├── __init__.py
│   │   ├── models.py              # Tenant, TenantFeatureFlag
│   │   ├── admin.py
│   │   ├── forms.py               # TenantForm, FeatureFlagFormSet
│   │   ├── urls.py
│   │   ├── views/
│   │   │   └── tenant_views.py    # Super Admin tenant management
│   │   ├── services/
│   │   │   └── tenant_service.py  # create_tenant, update_quotas, toggle_flags
│   │   └── tests/
│   └── accounts/
│       ├── __init__.py
│       ├── models.py              # User, UserRole, UserProfile, AuditLog
│       ├── admin.py
│       ├── forms.py               # OptiExamLoginForm, UserProfileForm, UserCreateForm
│       ├── urls.py
│       ├── views/
│       │   ├── auth_views.py      # Universal login, logout, redirect dispatcher
│       │   └── profile_views.py
│       ├── services/
│       │   ├── auth_service.py    # authenticate_and_route, record_audit_log
│       │   └── user_service.py    # provision_user, assign_role
│       └── tests/
├── static/
│   ├── css/
│   │   ├── optiexam-core.css      # CSS variables, typography, reset, grid
│   │   ├── optiexam-theme.css     # Dark/light glassmorphism tokens
│   │   └── components/
│   │       ├── navbar.css
│   │       ├── cards.css
│   │       ├── forms.css
│   │       ├── buttons.css
│   │       └── badges.css
│   ├── js/
│   │   └── optiexam-core.js       # Top-nav actions, fullscreen toggle, theme toggle
│   ├── fonts/
│   │   ├── inter/                 # Inter WOFF2 files
│   │   ├── outfit/                # Outfit WOFF2 files
│   │   └── jetbrains-mono/        # JetBrains Mono WOFF2 files
│   ├── icons/
│   │   └── lucide-sprite.svg      # Bundled local Lucide SVG sprite
│   └── img/
│       ├── optiexam-logo.svg
│       └── default-avatar.svg
└── templates/
    ├── base.html                  # Master HTML5 skeleton (zero CDN)
    ├── base_app.html              # Authenticated app shell with top-nav & notifications
    ├── includes/
    │   ├── top_nav.html           # Universal top-nav with fullscreen icon & timer pill
    │   ├── notification_drawer.html
    │   └── page_guide.html        # Contextual guide cards with colorful icons
    ├── accounts/
    │   ├── login.html             # Premium glassmorphic universal login page
    │   └── profile.html
    └── dashboards/
        └── super_admin.html       # SaaS Manager tenant matrix & health hub
```

---

## 3. Step-by-Step Implementation Tasks

### Task 1.1: Project Skeleton & Modular Settings
1. Create `requirements.txt` and `requirements-dev.txt` with pinned dependencies.
2. Initialize Django project in root directory `optiexam/`.
3. Split settings into `optiexam/settings/`:
   * `base.py`: Declares `INSTALLED_APPS` (with `apps.core`, `apps.tenants`, `apps.accounts`), `AUTH_USER_MODEL = 'accounts.User'`, `MIDDLEWARE` pipeline with `TenantResolutionMiddleware`, `TEMPLATES` context processors, logging configuration, and static/media paths.
   * `local.py`: Inherits `base.py`, sets `DEBUG = True`, uses SQLite `DATABASE_URL = sqlite:///db.sqlite3`.
   * `production.py`: Inherits `base.py`, sets `DEBUG = False`, parses PostgreSQL `DATABASE_URL`, configures connection pooling, strict HTTPS, and HSTS headers.
4. Verify environment parsing via `django-environ` reading `.env`.

### Task 1.2: 100% Offline Static Asset Architecture
1. Bundle local typography in `static/fonts/`:
   * `Inter` (Regular 400, Medium 500, SemiBold 600, Bold 700)
   * `Outfit` (Medium 500, Bold 700, ExtraBold 800)
   * `JetBrains Mono` (Regular 400, Bold 700)
2. Bundle `static/icons/lucide-sprite.svg` containing all required icons (`maximize`, `minimize`, `bell`, `moon`, `sun`, `user`, `shield`, `check`, `alert-triangle`, `clock`, `file-text`, `plus`, `settings`, `log-out`).
3. Author `static/css/optiexam-core.css` with `@font-face` declarations and CSS variable design tokens (`--color-primary: #4F46E5`, `--color-surface: #1E1E2E`, glassmorphism styles).
4. Author `static/js/optiexam-core.js` for fullscreen toggle API, theme switching (dark/light), and notification badge interactions.

### Task 1.3: Core Multi-Tenancy Engine (`apps/core` & `apps/tenants`)
1. Implement `TenantModelMixin` in `apps/core/models.py` with `tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE)`.
2. Implement `TenantQuerySet` with `.for_tenant(tenant)` and `TenantManager`.
3. Implement `TenantResolutionMiddleware` in `apps/core/middleware.py` resolving tenant from URL slug (`/{tenant_slug}/...`) or session cookie, attaching `request.tenant`.
4. Implement `Tenant` and `TenantFeatureFlag` models in `apps/tenants/models.py`.
5. Create `tenant_service.py` with `create_tenant()`, `toggle_feature_flag()`, `update_tier_quotas()`.

### Task 1.4: Custom User Model & 5-Tier RBAC Engine (`apps/accounts`)
1. Implement `UserRole` enum with 5 roles: `SUPER_ADMIN`, `DESIGNER`, `ITEM_WRITER`, `GRADER`, `PARTICIPANT`.
2. Implement custom `User(AbstractUser)` model in `apps/accounts/models.py` with `tenant` (nullable for Super Admin), `role`, `phone_number`, `avatar`, and convenience check methods (`is_super_admin()`, `is_designer()`, etc.).
3. Implement `UserProfile` model (registration number, department, batch year).
4. Implement `AuditLog` model (action, category, IP address, user agent, payload, timestamp).
5. Implement RBAC Class-Based View mixins in `apps/core/mixins.py`:
   * `SuperAdminRequiredMixin`
   * `DesignerRequiredMixin`
   * `ItemWriterRequiredMixin`
   * `GraderRequiredMixin`
   * `ParticipantRequiredMixin`
   * `TenantStaffRequiredMixin`

### Task 1.5: Global Template Context Processors with Caching
Implement the 5 specialized context processors in `apps/core/context_processors.py`:
1. `tenant_context`: Injects `current_tenant`, `tenant_name`, `tenant_logo`, `tenant_primary_color`, and cached `tenant_feature_flags` dict (5-min cache TTL).
2. `user_role_context`: Injects `is_super_admin`, `is_designer`, `is_item_writer`, `is_grader`, `is_participant`, `user_role_name`, `user_avatar`.
3. `notification_context`: Injects `unread_notifications_count` (cached with 60s TTL) and `recent_notifications` (top 5 unread).
4. `active_exam_context`: Injects `active_exam_attempt` if candidate is mid-exam.
5. `system_settings_context`: Injects `OPTIEXAM_VERSION`, `IS_OFFLINE_READY`, `ui_theme`, `is_dark_mode`.

### Task 1.6: Universal Login & Role-Based Routing
1. Create `OptiExamLoginForm` in `apps/accounts/forms.py`.
2. Build `LoginView` at `/auth/login/` rendering `templates/accounts/login.html` with modern glassmorphism design, brand logo, and responsive form controls.
3. Build `RoleRedirectView` that routes authenticated users dynamically:
   * `SUPER_ADMIN` → `/admin/saas/dashboard/`
   * `DESIGNER` → `/{tenant_slug}/dashboard/`
   * `ITEM_WRITER` → `/{tenant_slug}/questions/`
   * `GRADER` → `/{tenant_slug}/grading/`
   * `PARTICIPANT` → `/{tenant_slug}/lobby/`

### Task 1.7: Super Admin Complete CRUD & Advanced Interactive Matrix (`apps/tenants`)
1. **Full CRUD View Suite**:
   * `SuperAdminDashboardView`: High-density directory matrix with **single-line filter toolbar** (`.filter-row-single`), multi-field search (`q`), tier filter, status filter, `[Filter]` and `[Clear]` (`rotate-ccw`) icon buttons, two-way clickable column sorting (`{% sort_header %}`), full-featured windowed pagination (`{% include "includes/pagination.html" %}` with `10/25/50/100` page size), and **colorful icon-only action buttons** (`action-btn-inspect` with `eye`, `action-btn-edit` with `edit`, `action-btn-delete` with `trash-2`) with concise hover tooltips (`"Inspect"`, `"Edit"`, `"Delete"`).
   * `TenantCreateView` & `TenantUpdateView`: Balanced **two-column full-screen width smart form** (`<div class="grid grid-cols-2 gap-6">`) structured into 4 categorized cards (Identity, Quotas, Branding, Security) with 1-click color presets, auto-slugify, and full-width bottom actions bar.
   * `TenantDetailView`: Deep inspection cockpit for quotas, storage metrics, and 1-click feature flag icon toggles with concise tooltips (`"Enable"`, `"Disable"`).
   * `TenantDeleteView`: Safe deactivation / soft delete with confirmation view.
   * `TenantFeatureFlagToggleView`: AJAX 1-click feature toggle endpoint.
2. **Audit Log Explorer Hub (`AuditLogListView`)**:
   * Global and tenant-filtered event logs with single-line filter toolbar, IP search, category dropdown, and pagination.
3. **Tenant User Management Hub (`TenantUserListView`, `TenantUserCreateView`, `TenantUserUpdateView`)**:
   * Multi-role user administration with role filters, status badges, password reset, and deactivation.


### Task 1.8: Bulk Faculty & User CSV/Excel Import Hub (`apps/accounts`)
1. Implement `FacultyUserImportForm` and dedicated User Import View at `/{tenant_slug}/admin/users/import/`.
2. Build dynamic template downloader providing `sample_faculty_users.csv` and `sample_faculty_users.xlsx` with instructions.
3. Implement `import_faculty_users_service(file, tenant)`:
   * Dry-run validation of email, username uniqueness, and role choices (`ITEM_WRITER`, `GRADER`, `DESIGNER`).
   * Renders 10-row confirmation preview.
   * On confirmation: provisions users, generates activation tokens, and logs `DataImportJob`.

---



## 4. Detailed Data Models Implemented in Phase 1

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│         tenants.Tenant          │       │    tenants.TenantFeatureFlag    │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ id (PK)                         │◄──┐   │ id (PK)                         │
│ name (VARCHAR 200)              │   └───┤ tenant_id (FK)                  │
│ slug (SLUG 100, UNIQUE)         │       │ feature_key (VARCHAR 50)        │
│ domain (VARCHAR 255, NULL)      │       │ is_enabled (BOOLEAN)            │
│ tier (STARTER|PROF|ENTERPRISE)  │       │ updated_at (DATETIME)           │
│ is_active (BOOLEAN)             │       └─────────────────────────────────┘
│ max_concurrent_candidates (INT) │
│ logo (IMAGE)                    │       ┌─────────────────────────────────┐
│ primary_color (VARCHAR 7)       │       │       accounts.AuditLog         │
│ created_at / updated_at         │       ├─────────────────────────────────┤
└────────────────┬────────────────┘       │ id (PK)                         │
                 │                        │ tenant_id (FK, NULL)            │
                 │ 1:N                    │ user_id (FK, NULL)              │
                 ▼                        │ category (VARCHAR 20)           │
┌─────────────────────────────────┐       │ action (VARCHAR 150)            │
│          accounts.User          │       │ ip_address (IP)                 │
├─────────────────────────────────┤       │ user_agent (VARCHAR 255)        │
│ id (PK)                         │       │ payload (JSON)                  │
│ tenant_id (FK, NULL for SAAS)   │       │ timestamp (DATETIME)            │
│ username (VARCHAR 150, UNIQUE)  │       └─────────────────────────────────┘
│ email (EMAIL)                   │
│ role (5-tier UserRole)          │       ┌─────────────────────────────────┐
│ phone_number (VARCHAR 20)       │       │      accounts.UserProfile       │
│ avatar (IMAGE)                  │       ├─────────────────────────────────┤
│ is_verified (BOOLEAN)           │◄─────►│ user_id (OneToOneField)         │
│ is_active / is_staff            │  1:1  │ registration_number (VARCHAR 50)│
│ created_at / updated_at         │       │ department (VARCHAR 100)        │
└─────────────────────────────────┘       │ batch_year / specialization     │
                                          └─────────────────────────────────┘
```

---

## 5. UI/UX Design System Specifications

### 5.1 Master Template Hierarchy & Full Screen Width Layout
1. **Full-Screen Width Fluid Containers (`.container`, `.container-fluid`)**:
   * Uses `width: 100%; max-width: 100%;` with `28px` gutter padding to maximize horizontal screen real estate across all displays.
   * Tables, grids, and dashboards expand fluidly to fill 100% of the viewport width.
2. **`base.html`**: Zero-CDN HTML5 container. Loads local CSS tokens, fonts, and favicon. Defines blocks: `{% block title %}`, `{% block extra_css %}`, `{% block content %}`, `{% block extra_js %}`.
3. **`base_app.html`**: Extends `base.html`. Renders top navigation bar with tenant brand, active exam resume banner, theme toggle button, notification dropdown, and user profile badge.
4. **Page Guide Partial (`includes/page_guide.html`)**: Included at top of every admin page, rendering colorful icons and explanatory guidance text explaining options.

---


## 6. Verification & Automated Test Plan

### Test Suite Execution
```powershell
# Run Phase 1 verification tests
& "C:\venv\envoptiexam\Scripts\python.exe" -m pytest apps/core/tests apps/tenants/tests apps/accounts/tests -v --cov=apps/core --cov=apps/tenants --cov=apps/accounts
```

### Specific Test Cases to Implement:
1. `test_tenant_isolation_queryset`: Validates `Model.objects.for_tenant(tenant_a)` never returns records belonging to `tenant_b`.
2. `test_tenant_resolution_middleware`: Validates request with slug `nec` resolves `request.tenant` correctly, and invalid slug returns `403 Forbidden`.
3. `test_5_tier_rbac_mixins`: Validates each of the 5 role mixins grants access to authorized roles and denies unauthorized roles with `403`.
4. `test_zero_external_cdn_in_templates`: Static parser checking that rendered HTML templates contain 0 occurrences of `http://` or `https://` in `<link>` or `<script>` tags.
5. `test_super_admin_tenant_creation`: Validates Super Admin can provision a new tenant with initial feature flags and assign a Designer user.
6. `test_context_processors_caching`: Validates `tenant_context` reads from cache on second request and avoids database queries.

---

## 7. Definition of Done (DoD) for Phase 1
* [ ] Database migrations execute cleanly for `core`, `tenants`, and `accounts` on both SQLite and PostgreSQL.
* [ ] Universal login screen renders with 100% local assets and zero browser console errors.
* [ ] Super Admin can log in, view the SaaS dashboard, create a new institution (tenant), and provision a Designer.
* [ ] Role-based redirector accurately routes each of the 5 user roles to their respective home screen.
* [ ] All unit and isolation tests pass with ≥ 90% code coverage.
