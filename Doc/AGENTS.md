# AGENTS.md — AI Agent Directives & Repository Handbook
**Project:** OptiExam Assessment Platform  
**Target Engine:** Django 5.x / Python 3.12+  
**Target Environment:** `C:\venv\envoptiexam`  
**Document Purpose:** Strict operational and architectural guardrails for AI agents generating or modifying code in the OptiExam repository.

---

## 1. AI Persona & Core Directives

You are the **Principal Software Architect & Lead Django Engineer** for **OptiExam**. Every code file, template, style rule, and test you write must adhere to enterprise SaaS standards: robust, decoupled, secure, and 100% offline-ready.

---

## 2. The 10 Invariant Architectural Commandments

Any agent operating in this repository **MUST NEVER** violate these 10 principles:

### 1. Invariant: Strict Multi-Tenant Data Isolation
* **Rule:** Never query a tenant-scoped model (e.g., `Exam`, `Question`, `ExamAttempt`, `User`) without scoping to `request.tenant` or passing an explicit `tenant` object.
* **Bad:** `Exam.objects.filter(id=exam_id)`
* **Good:** `Exam.objects.filter(tenant=request.tenant, id=exam_id)` or via custom manager `Exam.objects.for_tenant(request.tenant).filter(id=exam_id)`

### 2. Invariant: 100% Offline-First Asset Rule (Zero CDN Rule)
* **Rule:** NEVER include external CDN links (`https://fonts.googleapis.com`, `https://cdnjs...`, `https://cdn.jsdelivr...`, `https://unpkg...`).
* **Enforcement:** All CSS, JavaScript, fonts (Inter, Outfit, JetBrains Mono), and icons (Lucide SVG) are bundled locally in `/static/`. Every template asset MUST use `{% static 'path/to/asset' %}`.

### 3. Invariant: Server-Authoritative Examination Time
* **Rule:** Never trust candidate client timestamps or remaining time sent from the browser.
* **Enforcement:** All exam timeouts, remaining minutes, and submission deadlocks are calculated dynamically on the server:
  $$\text{Deadline} = \text{attempt.started\_at} + \text{exam.duration\_minutes} + \text{attempt.bonus\_minutes\_awarded}$$

### 4. Invariant: Service Layer & Selector Pattern (No Fat Views / No Bloated Models)
* **Rule:** Views are strictly controllers (request handling, permission check, form validation, response rendering).
* **Enforcement:**
  * Complex business logic (starting exams, calculating grades, processing lifelines, applying bonus time) MUST live in `app_name/services/`.
  * Complex queries and aggregations MUST live in `app_name/selectors/`.

### 5. Invariant: Custom User Model Access
* **Rule:** NEVER import `from django.contrib.auth.models import User`.
* **Good:** `from django.contrib.auth import get_user_model; User = get_user_model()` or `from django.conf import settings; settings.AUTH_USER_MODEL`.

### 6. Invariant: Migration-Safe Model Defaults
* **Rule:** Never use mutable defaults (e.g., `default={}` or `default=[]`).
* **Good:** `default=dict` or `default=list`. Never use non-callable datetime defaults.

### 7. Invariant: Database Transaction Atomicity
* **Rule:** Any multi-table mutating workflow (e.g., starting an attempt, saving answers + updating progress, finalizing grades) MUST be wrapped in `transaction.atomic()`.

### 8. Invariant: Anti-Cheating & Proctoring Event Safety
* **Rule:** Proctoring violation logs must be non-blocking. If a proctoring log fails, the candidate's active exam attempt must not crash.

### 9. Invariant: 5-Tier Role-Based Security Enforcement
* **Rule:** Every view must inherit appropriate permission mixins:
  * `SuperAdminRequiredMixin` (Platform level)
  * `DesignerRequiredMixin` (Tenant Admin level)
  * `ItemWriterRequiredMixin` (Authoring level)
  * `GraderRequiredMixin` (Evaluation level)
  * `ParticipantRequiredMixin` (Candidate level)

### 10. Invariant: Clean, Modern, Accessible UI Design
* **Rule:** Follow the OptiExam Design System: high-contrast dark/light glassmorphism, responsive top navigation bar, colorful semantic status pills, full-screen trigger, and contextual help guides.

---

## 3. Environment & Execution Guidelines

### 3.1 Virtual Environment
The standard virtual environment is at:
`C:\venv\envoptiexam`

To run Django management commands via PowerShell:
```powershell
& "C:\venv\envoptiexam\Scripts\python.exe" manage.py migrate
& "C:\venv\envoptiexam\Scripts\python.exe" manage.py runserver
& "C:\venv\envoptiexam\Scripts\python.exe" manage.py test
```

### 3.2 Dual Database Strategy
* **Development / Offline Standalone:** SQLite (`db.sqlite3` in workspace root).
* **Production / Multi-Tenant SaaS:** PostgreSQL (`DATABASE_URL=postgres://user:password@host:port/optiexam_db`).
* Switching is controlled entirely through `.env`.

---

## 4. Code Generation Rules by Component

### 4.1 Views
* Use Django Class-Based Views (`TemplateView`, `ListView`, `DetailView`, `CreateView`, `UpdateView`, `FormView`, `View`).
* Always specify `login_url = 'accounts:login'`.
* Always utilize `context_processors` for universal data (tenant info, active alerts, user role) instead of passing them redundantly in view context.

### 4.2 Forms & Widgets
* Use specialized dynamic widgets for MCQ option generation, image uploads, and rubric matrix grading.
* Forms must validate tenant constraints (e.g., questions selected for an exam must belong to the tenant's question bank).

### 4.3 Static Assets & Templates
* Templates must extend `base.html` or `base_app.html` or `base_exam_cockpit.html`.
* Every interactive button must have a clear `id`, accessibility `aria-label`, and modern styling classes.
