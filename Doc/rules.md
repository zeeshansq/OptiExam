# Project Rules & Development Standards — OptiExam
**Document Version:** 1.0.0  
**Scope:** Engineering Guidelines, Code Conventions, Security Protocols, and Offline Standards  

---

## 1. Code Standards & Python Conventions

### 1.1 Python 3.12+ & Django Standards
1. **Type Annotations:** All service functions, selectors, model methods, and helper utilities must be fully type-hinted.
   ```python
   # Correct
   def award_bonus_time(attempt_id: int, bonus_minutes: int, reason: str) -> ExamAttempt:
       ...
   ```
2. **Explicit Imports:** Never use wildcard imports (`from module import *`). Group imports following PEP 8: Standard library, third-party packages, internal Django apps.
3. **Docstrings:** Use Google-style or Sphinx-style docstrings on all service functions and complex model methods.
4. **Code Quality:** Format code using `ruff` or `black` with a maximum line length of 100 characters.

---

## 2. Multi-Tenancy & Query Isolation Rules

### 2.1 The `TenantModelMixin` Pattern
Every model that belongs to an institution/tenant must inherit from `TenantModelMixin`:
```python
# core/models.py
from django.db import models

class TenantModelMixin(models.Model):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        db_index=True
    )

    class Meta:
        abstract = True
```

### 2.2 Query Isolation Rules
* Never perform global queries on tenant data.
* Views and API endpoints must scope all queries to `request.tenant` or `request.user.tenant`.
* Use custom tenant managers (`for_tenant(tenant)`) to prevent cross-tenant data leaks.

---

## 3. 100% Offline Asset & Styling Rules

### 3.1 Zero External Request Policy
* **Forbidden:**
  ```html
  <!-- FORBIDDEN IN OPTIEXAM -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  ```
* **Required:**
  ```html
  <!-- REQUIRED IN OPTIEXAM -->
  <link rel="stylesheet" href="{% static 'css/optiexam-core.css' %}">
  <link rel="stylesheet" href="{% static 'css/optiexam-theme.css' %}">
  <script src="{% static 'js/optiexam-core.js' %}"></script>
  ```

### 3.2 Local Fonts & Icons
* Fonts reside in `/static/fonts/` (Inter, Outfit, JetBrains Mono in `.woff2` format).
* Icons reside in `/static/icons/` as SVG sprites or bundled inline icons.

---

## 4. Anti-Cheating & Proctoring Integrity Rules

1. **Client Untrusted Principle:** The client browser is assumed to be an untrusted environment.
2. **Server-Authoritative Clock:** The server maintains and enforces the exam deadline. Time sent by the client is treated solely as an indicator of local latency.
3. **Heartbeat Frequency:** The client sends an asynchronous heartbeat every 15 seconds. If the server does not receive a heartbeat for > 60 seconds, the student's status changes to `DISCONNECTED` in the Live Ops room.
4. **Violation Escalation:** Tab switches, fullscreen exits, and blur events increment an in-memory violation counter and log to `ProctoringLog`. After *N* violations (set by Designer), the exam auto-submits.

---

## 5. Security & Access Control Rules

### 5.1 5-Tier User Role Constants
All user authorization logic must reference the canonical `UserRole` enum:
```python
# accounts/models.py
from django.db import models

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin (SaaS Manager)'
    DESIGNER = 'DESIGNER', 'Designer (Tenant Admin)'
    ITEM_WRITER = 'ITEM_WRITER', 'Item Writer (Subject Expert)'
    GRADER = 'GRADER', 'Grader (Evaluation Officer)'
    PARTICIPANT = 'PARTICIPANT', 'Participant (Student/Candidate)'
```

### 5.2 View Permission Mixins
All Class-Based Views must inherit from `LoginRequiredMixin` and the specific role mixin:
* `SuperAdminRequiredMixin`
* `DesignerRequiredMixin`
* `ItemWriterRequiredMixin`
* `GraderRequiredMixin`
* `ParticipantRequiredMixin`

---

## 6. Database Transaction & Data Integrity Rules

1. **Atomic Operations:** Wrap multi-record operations in `transaction.atomic()`:
   * Exam start initialization.
   * Exam submission & auto-scoring.
   * Grader batch assignment.
   * Final grade calculation.
2. **Optimistic Locking:** Scoring updates must check the version or timestamp of the record to avoid race conditions.
3. **Cascading Safety:** Avoid accidental mass deletion. Use `PROTECT` on critical links (e.g., `Question` linked to an `AttemptAnswer`).
