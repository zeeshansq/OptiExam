# Project Layout & File System Architecture — OptiExam
**Document Version:** 2.0.0  
**Project:** OptiExam Assessment Platform  
**Audit:** 2026-08-14 — Added `requirements.txt`, `.gitignore`, `conftest.py`, `middleware.py`, `signals.py`, `management/commands/`, `logs/`, `locale/`.

---

## 1. Master Workspace Directory Tree

```
c:\py-projects\OptiExam\
├── .env.example                         # Reference environment template (committed)
├── .env                                 # Active environment config (git-ignored!)
├── .gitignore                           # Python/Django gitignore
├── manage.py                            # Django management CLI entrypoint
├── requirements.txt                     # Production dependencies (pinned versions)
├── requirements-dev.txt                 # Development-only dependencies
├── conftest.py                          # Pytest fixtures and global test config
├── pytest.ini                           # Pytest configuration
├── pyproject.toml                       # ruff + black configuration
├── logs/                                # Runtime application logs (git-ignored)
│   └── optiexam.log
├── Doc/                                 # Master System Documentation
│   ├── PRD.md                           # Product Requirements Document
│   ├── DFD.md                           # Data Flow Diagrams (Mermaid)
│   ├── AGENTS.md                        # AI Agent Directives & Handbook
│   ├── rules.md                         # Code & Development Standards
│   ├── models_schema.md                 # Complete Django ORM Model Schema
│   ├── app_structure.md                 # App Architecture & Service Layer
│   ├── custom_instructions.txt          # AI Agent Compact System Prompt
│   ├── api_spec.md                      # REST API Specification
│   ├── project_layout.md                # Directory Layout (this file)
│   ├── models_and_forms.md              # Forms, FormSets, Dynamic Widgets
│   └── context_processors.md           # Global Template Context Processors
├── optiexam/                            # Django Project Configuration Root
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py                          # Root URL dispatcher
│   └── settings/
│       ├── __init__.py                  # Imports from local.py or production.py
│       ├── base.py                      # Core: INSTALLED_APPS, middleware, auth, static
│       ├── local.py                     # SQLite + Debug Toolbar + console email
│       └── production.py               # PostgreSQL + connection pool + strict security
├── apps/                                # Django Domain Application Package
│   ├── __init__.py
│   ├── core/                            # Foundation: mixins, middleware, tags, utils
│   │   ├── models.py                    # TenantModelMixin (abstract)
│   │   ├── managers.py                  # TenantQuerySet, TenantManager
│   │   ├── middleware.py                # TenantResolutionMiddleware
│   │   ├── mixins.py                    # RBAC CBV Mixins (all 5 roles)
│   │   ├── permissions.py               # DRF Permission classes
│   │   ├── context_processors.py        # 5 global context processors
│   │   ├── templatetags/
│   │   │   ├── __init__.py
│   │   │   ├── optiexam_tags.py         # Custom template tags (e.g. offline_static)
│   │   │   └── icon_tags.py             # SVG icon inclusion helper tag
│   │   └── utils.py                     # Shared utilities (seed shuffler, token gen)
│   ├── tenants/                         # Multi-tenant management
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── urls.py                      # app_name = 'tenants'
│   │   ├── views/
│   │   │   └── tenant_views.py
│   │   ├── services/
│   │   │   └── tenant_service.py
│   │   └── tests/
│   ├── accounts/                        # 5-tier User model, Auth, Audit
│   │   ├── models.py                    # User(AbstractUser), UserProfile, AuditLog
│   │   ├── admin.py
│   │   ├── forms.py                     # OptiExamLoginForm, UserProfileForm
│   │   ├── urls.py                      # app_name = 'accounts'
│   │   ├── views/
│   │   │   ├── auth_views.py
│   │   │   └── profile_views.py
│   │   ├── services/
│   │   │   └── auth_service.py
│   │   └── tests/
│   ├── exams/                           # Exam blueprints, sections, Live Ops
│   │   ├── models.py                    # Exam, ExamSection, ExamQuestionAssignment
│   │   │                                # ExamParticipantRoster, ExamLifelineConfig
│   │   │                                # ExamLiveEvent
│   │   ├── admin.py
│   │   ├── forms.py                     # ExamForm, ExamSectionFormSet, LifelineFormSet
│   │   │                                # RosterImportForm, GraderAllocationForm
│   │   ├── urls.py                      # app_name = 'exams'
│   │   ├── views/
│   │   │   ├── blueprint_views.py       # Exam creation/editing (Designer)
│   │   │   ├── roster_views.py          # Roster import/management
│   │   │   └── live_ops_views.py        # Real-time control room (Designer)
│   │   ├── services/
│   │   │   ├── exam_lifecycle_service.py
│   │   │   ├── live_ops_service.py      # grant_bonus_time, broadcast, force_controls
│   │   │   └── roster_service.py        # CSV import, manual add, validation
│   │   ├── selectors/
│   │   │   └── exam_selectors.py
│   │   └── tests/
│   ├── questions/                       # Question banks, 5 types, rubrics
│   │   ├── models.py                    # QuestionBank, Question, QuestionOption, QuestionRubric
│   │   ├── forms.py                     # MCQQuestionForm, EssayQuestionForm, OptionFormSet, RubricFormSet
│   │   ├── urls.py                      # app_name = 'questions'
│   │   ├── views/
│   │   │   └── authoring_views.py
│   │   ├── services/
│   │   │   └── question_service.py
│   │   └── tests/
│   ├── submissions/                     # Candidate cockpit, heartbeat, anti-cheating
│   │   ├── models.py                    # ExamAttempt, AttemptAnswer, ProctoringLog, AttemptLifelineUsage
│   │   ├── urls.py                      # app_name = 'submissions'
│   │   ├── views/
│   │   │   ├── lobby_views.py           # Exam lobby (Participant)
│   │   │   └── cockpit_views.py         # Live exam cockpit
│   │   ├── services/
│   │   │   ├── attempt_service.py       # start_attempt, resume_attempt
│   │   │   ├── heartbeat_service.py     # process_heartbeat, offline_sync
│   │   │   ├── submission_service.py    # submit_attempt, auto_submit_expired
│   │   │   └── lifeline_service.py      # apply_lifeline, validate_lifeline
│   │   ├── selectors/
│   │   │   └── attempt_selectors.py
│   │   ├── signals.py                   # Post-submission notifications
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── auto_submit_expired.py
│   │   └── tests/
│   ├── grading/                         # Batched evaluation, rubrics, moderation
│   │   ├── models.py                    # GraderAllocation, QuestionScore, GradeModeration
│   │   ├── forms.py                     # QuestionScoreForm, GraderAllocationForm
│   │   ├── urls.py                      # app_name = 'grading'
│   │   ├── views/
│   │   │   ├── allocation_views.py      # Batch assignment (Designer)
│   │   │   └── evaluation_views.py      # Split-screen grading cockpit (Grader)
│   │   ├── services/
│   │   │   ├── grading_service.py       # save_score, finalize_evaluation
│   │   │   └── scoring_service.py       # auto_grade_mcq, compute_total_score
│   │   ├── selectors/
│   │   │   └── grader_selectors.py
│   │   └── tests/
│   └── notifications/                   # In-app alerts and live broadcasts
│       ├── models.py                    # Notification, BroadcastAlert
│       ├── urls.py                      # app_name = 'notifications'
│       ├── views/
│       │   └── notification_views.py
│       ├── services/
│       │   └── notification_service.py  # dispatch_notification, dispatch_exam_alert
│       └── tests/
├── static/                              # 100% Offline-Ready Static Assets (no CDN)
│   ├── css/
│   │   ├── optiexam-core.css            # Reset, CSS variables, @font-face declarations
│   │   ├── optiexam-theme.css           # Dark/light glassmorphism theme
│   │   ├── components/
│   │   │   ├── navbar.css               # Top navigation bar styles
│   │   │   ├── cards.css                # Dashboard card styles
│   │   │   ├── forms.css                # Form input, select, checkbox styles
│   │   │   ├── buttons.css              # Button variants (primary, danger, ghost)
│   │   │   ├── badges.css               # Status pills, notification badges
│   │   │   └── modals.css               # Modal dialog overlays
│   │   ├── cockpit.css                  # Fullscreen exam cockpit styles
│   │   ├── grading.css                  # Split-screen grader cockpit styles
│   │   └── print.css                    # Print-safe scorecard styles
│   ├── js/
│   │   ├── optiexam-core.js             # Top-nav, fullscreen, theme toggle
│   │   ├── anti-cheat-shield.js         # Event shields (copy/paste/blur/key lock)
│   │   ├── heartbeat-sync.js            # 15s auto-save + offline localStorage queue
│   │   ├── exam-cockpit.js              # Question palette, navigation, timer
│   │   ├── lifeline-engine.js           # Lifeline UI (50:50 cross-out, skip, hint)
│   │   ├── grader-cockpit.js            # Rubric sliders, mark summation
│   │   └── live-ops.js                  # Designer real-time candidate matrix polling
│   ├── fonts/
│   │   ├── inter/
│   │   │   ├── Inter-Regular.woff2
│   │   │   ├── Inter-Medium.woff2
│   │   │   ├── Inter-SemiBold.woff2
│   │   │   └── Inter-Bold.woff2
│   │   ├── outfit/
│   │   │   ├── Outfit-Medium.woff2
│   │   │   ├── Outfit-Bold.woff2
│   │   │   └── Outfit-ExtraBold.woff2
│   │   └── jetbrains-mono/
│   │       ├── JetBrainsMono-Regular.woff2
│   │       └── JetBrainsMono-Bold.woff2
│   ├── icons/
│   │   └── lucide-sprite.svg            # Local SVG sprite of all Lucide icons
│   └── img/
│       ├── optiexam-logo.svg
│       ├── default-avatar.svg
│       └── empty-state.svg
├── media/                               # User-uploaded content (git-ignored)
│   ├── tenants/logos/
│   ├── accounts/avatars/
│   └── questions/diagrams/
└── templates/                           # Django Template Hierarchy
    ├── base.html                        # HTML5 skeleton (offline assets, meta SEO)
    ├── base_app.html                    # App shell: top-nav, notifications, breadcrumbs
    ├── base_exam_cockpit.html           # Lockdown fullscreen examination screen
    ├── includes/
    │   ├── top_nav.html                 # Top navigation bar partial
    │   ├── notification_drawer.html     # Notification dropdown partial
    │   └── page_guide.html              # Contextual help text + icon partial
    ├── accounts/
    │   ├── login.html
    │   └── profile.html
    ├── dashboards/
    │   ├── super_admin.html
    │   ├── designer.html
    │   ├── item_writer.html
    │   ├── grader.html
    │   └── participant.html
    ├── exams/
    │   ├── exam_list.html
    │   ├── exam_form.html
    │   ├── exam_detail.html
    │   ├── exam_lobby.html
    │   ├── live_ops.html
    │   └── roster_import.html
    ├── questions/
    │   ├── question_bank_list.html
    │   ├── question_list.html
    │   ├── question_form_mcq.html
    │   ├── question_form_image_mcq.html
    │   └── question_form_essay.html
    ├── grading/
    │   ├── allocation_list.html
    │   ├── allocation_form.html
    │   └── grading_cockpit.html
    └── submissions/
        ├── exam_lobby.html
        ├── exam_cockpit.html
        └── exam_result.html
```

---

## 2. Settings Configuration Strategy

| File | Purpose | Database | Debug |
|---|---|---|---|
| `settings/base.py` | Shared: INSTALLED_APPS, middleware, auth, static, templates, logging | — | — |
| `settings/local.py` | Local dev / offline lab | SQLite | `True` + Debug Toolbar |
| `settings/production.py` | Production SaaS | PostgreSQL + conn pooling | `False` + Strict Security |

**`INSTALLED_APPS` order in `base.py`:**
```python
INSTALLED_APPS = [
    # Django Core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # OptiExam Apps (order matters: core first)
    'apps.core',
    'apps.tenants',
    'apps.accounts',
    'apps.exams',
    'apps.questions',
    'apps.submissions',
    'apps.grading',
    'apps.notifications',
]
AUTH_USER_MODEL = 'accounts.User'
```

---

## 3. Python Package Requirements

### `requirements.txt` (Production)
```
# Core Framework
Django>=5.0,<6.0
django-environ>=0.11.2

# Database
psycopg2-binary>=2.9.9   # PostgreSQL driver (disabled in SQLite mode)

# Image Processing
Pillow>=10.4.0

# Excel & Bulk Data Import Ingestion
openpyxl>=3.1.5

# Date/Time Utilities
python-dateutil>=2.9.0

# Security
cryptography>=42.0.0      # AES encryption for offline attempt cache tokens

```

### `requirements-dev.txt` (Development Only)
```
-r requirements.txt
pytest>=8.0
pytest-django>=4.8
pytest-cov>=5.0
factory-boy>=3.3          # Test data factories
black>=24.0
ruff>=0.4
mypy>=1.10
django-debug-toolbar>=4.3
```

---

## 4. `pyproject.toml` (Ruff & Black Config)
```toml
[tool.black]
line-length = 100
target-version = ['py312']

[tool.ruff]
line-length = 100
target-version = "py312"
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "optiexam.settings.local"
python_files = ["test_*.py"]
addopts = "--reuse-db"
```

---

## 5. `.gitignore` (Key Entries)
```
# Environment
.env
*.env

# Database
db.sqlite3

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Media (user uploads)
media/

# Logs
logs/*.log

# Static (collected)
staticfiles/

# IDE
.vscode/
.idea/
*.swp
```
