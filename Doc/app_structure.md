# Django Application Structure & Service Layer Architecture — OptiExam
**Document Version:** 1.0.0  
**Project:** OptiExam Assessment Platform  
**Target Architecture:** Modular Django Apps with Dedicated Service & Selector Layers  

---

## 1. High-Level Modular App Architecture

OptiExam is partitioned into **8 cohesive, loosely coupled Django apps**:

```
optiexam/
├── core/            # Base mixins, tenant middleware, offline static tags, DataImportJob & template services
├── tenants/         # Multi-tenant management, institutional branding, feature flags
├── accounts/        # Custom 5-tier User model, RBAC mixins, authentication & audit, faculty bulk import
├── exams/           # Exam blueprints, sections, scheduling, lifelines, Live Ops, roster bulk import
├── questions/       # Question banks, 5 question types, image diagrams, rubric criteria, question bank bulk import
├── submissions/     # Candidate exam cockpit, heartbeat sync, anti-cheating, crash recovery
├── grading/         # Batched candidate allocation, split-screen evaluation, rubrics
└── notifications/   # In-app top-nav alerts, real-time supervisor broadcasts

```

---

## 2. Directory Layout Within Each App

Every app follows a strict modular structure separating controllers (views), write business logic (services), and read queries (selectors):

```
app_name/
├── __init__.py
├── admin.py             # Django admin integration
├── apps.py              # AppConfig registration
├── models.py            # Model definitions & simple properties
├── managers.py          # Custom QuerySets and Model Managers
├── forms.py             # Django Forms, FormSets, and Custom Widgets
├── urls.py              # URL routing
├── views/               # Class-Based Views (organized by role or feature)
│   ├── __init__.py
│   ├── dashboard_views.py
│   └── action_views.py
├── services/            # Pure Python business logic (MUTATIONS / WRITES)
│   ├── __init__.py
│   └── exam_lifecycle_service.py
├── selectors/           # Pure Python query logic (READS / AGGREGATIONS)
│   ├── __init__.py
│   └── candidate_attempt_selectors.py
├── templates/
│   └── app_name/        # Scoped HTML templates
└── tests/               # Unit, integration, and isolation tests
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_views.py
```

---

## 3. Separation of Concerns: Fat Models vs. Service Layer vs. Selectors

| Layer | Primary Responsibility | Permitted Actions | Forbidden Actions |
|---|---|---|---|
| **Views / Controllers** | HTTP Request handling, authentication/role validation, rendering templates or JSON. | Call Form `.is_valid()`, call Services, call Selectors. | Direct heavy ORM mutation logic, sending emails, external system calls. |
| **Services (`services/`)** | Business workflow execution, state transitions, transactions. | `@transaction.atomic`, mutating multiple models, creating audit logs, dispatching alerts. | Directly rendering HTTP templates, accessing `request` object directly. |
| **Selectors (`selectors/`)** | High-performance queries, complex aggregations, filtering. | `.select_related()`, `.prefetch_related()`, `.annotate()`, `.aggregate()`. | Modifying database records (`.save()`, `.update()`, `.delete()`). |
| **Models (`models.py`)** | Field definitions, table constraints, simple computed properties. | `@property`, `__str__`, clean validation, simple state checks (`is_active`). | Orchestrating multi-model business logic or calling other app services. |
| **Managers (`managers.py`)** | Common reusable queryset filters (e.g. `for_tenant()`, `active()`). | Custom `.filter()`, `.exclude()`. | Complex multi-stage business workflows. |

---

## 4. Concrete Service & Selector Implementation Examples

### 4.1 Service Example: Live Time Extension Injection
```python
# exams/services/live_ops_service.py
from django.db import transaction
from django.utils import timezone
from exams.models import Exam, ExamLiveEvent
from submissions.models import ExamAttempt
from notifications.services.notification_service import dispatch_exam_alert

@transaction.atomic
def grant_bonus_time_to_exam(
    exam: Exam,
    bonus_minutes: int,
    dispatched_by_user,
    reason: str = "Supervisor Adjustment"
) -> int:
    """
    Grants extra time to all active candidates in a live exam.
    Returns the count of affected active attempts.
    """
    # 1. Log Live Ops Event
    ExamLiveEvent.objects.create(
        exam=exam,
        event_type=ExamLiveEvent.EventType.ADD_TIME,
        target_type='ALL',
        data_payload={'bonus_minutes': bonus_minutes, 'reason': reason},
        created_by=dispatched_by_user
    )

    # 2. Update active attempts
    active_attempts = ExamAttempt.objects.filter(
        exam=exam,
        status=ExamAttempt.Status.IN_PROGRESS
    )
    
    updated_count = 0
    for attempt in active_attempts:
        attempt.bonus_minutes_awarded += bonus_minutes
        attempt.save(update_fields=['bonus_minutes_awarded', 'updated_at'])
        
        # 3. Trigger In-App Notification
        dispatch_exam_alert(
            tenant=exam.tenant,
            recipient=attempt.participant,
            title="Extra Time Awarded",
            message=f"Supervisor added {bonus_minutes} minutes to your examination. {reason}"
        )
        updated_count += 1

    return updated_count
```

### 4.2 Selector Example: Grader Workload & Candidate Queue
```python
# grading/selectors/grader_selectors.py
from typing import Iterable
from django.db.models import Count, Q
from grading.models import GraderAllocation
from submissions.models import ExamAttempt

def get_assigned_attempts_for_grader(allocation: GraderAllocation) -> Iterable[ExamAttempt]:
    """
    Retrieves the candidate attempts assigned to a specific grader allocation batch
    with pre-fetched answers and anonymized presentation.
    """
    attempts = (
        ExamAttempt.objects
        .filter(
            exam=allocation.exam,
            status__in=[ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.AUTO_SUBMITTED, ExamAttempt.Status.GRADED]
        )
        .order_by('id')[allocation.candidate_range_start - 1 : allocation.candidate_range_end]
    )
    return attempts.prefetch_related('answers', 'answers__question', 'answers__score_record')
```

---

## 5. Custom Managers & Tenant QuerySet Pattern

```python
# core/managers.py
from django.db import models

class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)

class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    pass
```

All models inheriting `TenantModelMixin` will automatically provide:
```python
# Clean and concise querying across all apps:
Exam.objects.for_tenant(request.tenant).filter(status='IN_PROGRESS')
```
