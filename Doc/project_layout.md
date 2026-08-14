# Project Layout & File System Architecture — OptiExam
**Document Version:** 1.0.0  
**Project:** OptiExam Assessment Platform  
**Target Environment:** Python 3.12+ / Django 5.x / `C:\venv\envoptiexam`  

---

## 1. Master Workspace Directory Tree

```
c:\py-projects\OptiExam\
├── .env.example                     # Reference environment configuration
├── .env                             # Active environment configuration (git-ignored)
├── .gitignore                       # Standard Python/Django gitignore
├── manage.py                        # Django management CLI entrypoint
├── requirements.txt                 # Project dependencies
├── Doc/                             # Master System Documentation & Architectural Specs
│   ├── PRD.md                       # Product Requirements Document
│   ├── DFD.md                       # Data Flow Diagrams
│   ├── AGENTS.md                    # AI Agent Directives & Handbook
│   ├── rules.md                     # Code, Security, & Offline Standards
│   ├── models_schema.md             # Complete Django ORM Model Schema
│   ├── app_structure.md             # App Structure & Service Layer Architecture
│   ├── custom_instructions.txt      # AI Agent Strict Custom Instructions
│   ├── api_spec.md                  # REST API Specification
│   ├── project_layout.md            # Directory Layout & File Hierarchy
│   ├── models_and_forms.md          # Models, Forms, & Dynamic Widgets Guide
│   └── context_processors.md        # Global Template Context Processors
├── optiexam/                        # Project Core Settings & Configuration Root
│   ├── __init__.py
│   ├── asgi.py                      # ASGI configuration for async events
│   ├── wsgi.py                      # WSGI configuration
│   ├── urls.py                      # Root URL routing dispatcher
│   └── settings/                    # Modular Django Settings
│       ├── __init__.py
│       ├── base.py                  # Base configuration & installed apps
│       ├── local.py                 # SQLite / Dev configuration
│       └── production.py            # PostgreSQL / Production SaaS configuration
├── apps/                            # Pluggable Django Domain Apps
│   ├── core/                        # Tenant mixins, template tags, utilities
│   ├── tenants/                     # Tenant routing, feature flags, branding
│   ├── accounts/                    # 5-tier User model, auth views, audit
│   ├── exams/                       # Exam blueprints, sections, Live Ops
│   ├── questions/                   # Question banks, 5 question types, rubrics
│   ├── submissions/                 # Candidate cockpit, heartbeat sync, anti-cheating
│   ├── grading/                     # Batched grader allocations, split-screen evaluation
│   └── notifications/               # In-app top-nav notification center
├── static/                          # 100% Offline-Ready Static Bundled Assets
│   ├── css/
│   │   ├── optiexam-core.css        # Base reset, typography, CSS variables
│   │   ├── optiexam-theme.css       # Dark/light glassmorphism theme rules
│   │   ├── components/              # Top-nav, modals, cards, badges, tooltips
│   │   │   ├── navbar.css
│   │   │   ├── cards.css
│   │   │   └── forms.css
│   │   ├── cockpit.css              # Fullscreen examination cockpit UI
│   │   └── grading.css              # Split-screen grader cockpit UI
│   ├── js/
│   │   ├── optiexam-core.js         # Top-nav, notifications, fullscreen helper
│   │   ├── anti-cheat-shield.js     # Event shield (copy/paste/blur/key lock)
│   │   ├── heartbeat-sync.js        # 15s auto-save sync & offline cache queue
│   │   ├── exam-cockpit.js          # Question palette navigation & lifelines
│   │   └── grader-cockpit.js        # Rubric scoring sliders & auto-summation
│   ├── fonts/                       # Bundled WOFF2 Typography (Zero CDN)
│   │   ├── inter/                   # Inter Regular, Medium, SemiBold, Bold
│   │   ├── outfit/                  # Outfit Medium, Bold, ExtraBold (Headings)
│   │   └── jetbrains-mono/          # JetBrains Mono (Code/Equations)
│   ├── icons/                       # Local Iconography
│   │   ├── lucide-sprite.svg        # Local SVG Icon Sprite Sheet
│   │   └── icons.svg
│   └── img/                         # System Branding & Placeholder Images
│       ├── optiexam-logo.svg
│       ├── default-avatar.svg
│       └── empty-state.svg
├── media/                           # User-Uploaded Content (Diagrams, Logos)
│   ├── tenants/logos/
│   ├── accounts/avatars/
│   └── questions/diagrams/
└── templates/                       # Universal & App Template Hierarchies
    ├── base.html                    # Universal HTML5 skeleton (offline assets only)
    ├── base_app.html                # App shell: Top-nav, notifications, breadcrumbs
    ├── base_exam_cockpit.html       # Locked distraction-free examination screen
    ├── accounts/
    │   ├── login.html               # Modern universal login page
    │   └── profile.html             # Profile & security settings
    ├── dashboards/                  # Specialized Dashboards for the 5 User Roles
    │   ├── super_admin.html         # SaaS health, tenant provisioning
    │   ├── designer.html            # Exam blueprints, roster, live ops
    │   ├── item_writer.html         # Question authoring studio
    │   ├── grader.html              # Assigned batches & SLA tracker
    │   └── participant.html         # Candidate lobby & scorecards
    ├── exams/
    │   ├── exam_list.html
    │   ├── exam_form.html           # Multi-step blueprint creation
    │   ├── exam_lobby.html          # Pre-exam instructions & countdown
    │   └── live_ops.html            # Real-time exam command center
    ├── questions/
    │   ├── question_bank_list.html
    │   ├── question_form_mcq.html
    │   ├── question_form_image.html
    │   └── question_form_essay.html
    ├── grading/
    │   ├── allocation_list.html
    │   └── grading_cockpit.html     # Split-screen evaluation studio
    └── notifications/
        └── notification_drawer.html # Top-nav dropdown alert list
```

---

## 2. Settings Configuration Strategy

The configuration is modularized in `optiexam/settings/`:
* `base.py`: Declares `INSTALLED_APPS`, middleware pipeline, custom user model `AUTH_USER_MODEL = 'accounts.User'`, template context processors, and static directories.
* `local.py`: Uses SQLite (`db.sqlite3`), enables debug toolbar, and outputs emails to console.
* `production.py`: Reads `DATABASE_URL` for PostgreSQL, enables connection pooling, strict security headers, and secure cookie flags.
