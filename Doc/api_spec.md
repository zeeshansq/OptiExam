# REST API Specification — OptiExam
**Document Version:** 2.0.0  
**Base URL:** `/api/v1/`  
**Authentication:** Django Session Auth + CSRF Token (web) / Bearer Token (API clients)  
**Required Headers:**
```
Content-Type:   application/json
X-Tenant-Slug:  <tenant_slug>
X-CSRFToken:    <csrf_token>       (session auth only)
Authorization:  Bearer <token>     (token auth only)
```

---

## Standard Error Response Schema

All error responses follow this canonical structure:

```json
{
  "status": "error",
  "code": "EXAM_NOT_FOUND",
  "message": "No exam found with the given ID for your tenant.",
  "detail": {},
  "timestamp": "2026-09-01T09:00:00Z"
}
```

**Common Error Codes:**

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid request payload |
| 401 | `UNAUTHENTICATED` | Not logged in |
| 403 | `PERMISSION_DENIED` | Role not authorized for this action |
| 403 | `TENANT_MISMATCH` | Resource belongs to different tenant |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `ATTEMPT_ALREADY_EXISTS` | Candidate already has an active/submitted attempt |
| 410 | `EXAM_WINDOW_CLOSED` | Exam schedule window has expired |
| 422 | `ROSTER_NOT_ENROLLED` | Participant not in exam's roster |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `SERVER_ERROR` | Internal server error |

---

## 1. Authentication Endpoints (`/api/v1/auth/`)

### 1.1 `POST /api/v1/auth/login/`
Authenticates user, returns session cookie and CSRF token.

**Request:**
```json
{
  "username": "ali.hassan",
  "password": "SecurePass123!",
  "remember_me": true
}
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "user_id": 842,
    "username": "ali.hassan",
    "full_name": "Ali Hassan",
    "role": "PARTICIPANT",
    "tenant_slug": "engineering-college",
    "tenant_name": "National Engineering College",
    "redirect_url": "/dashboard/"
  }
}
```

---

### 1.2 `POST /api/v1/auth/logout/`
Ends the authenticated session.

**Response `200 OK`:** `{ "status": "success", "message": "Logged out successfully." }`

---

### 1.3 `GET /api/v1/auth/me/`
Returns the current authenticated user's profile and role context.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "user_id": 842,
    "username": "ali.hassan",
    "full_name": "Ali Hassan",
    "email": "ali@nec.edu.pk",
    "role": "PARTICIPANT",
    "role_display": "Participant (Student/Candidate)",
    "tenant_slug": "engineering-college",
    "avatar_url": "/media/accounts/avatars/ali_hassan.jpg",
    "is_verified": true
  }
}
```

---

## 2. Super Admin Endpoints (`/api/v1/admin/`)
> **Required Role:** `SUPER_ADMIN`

### 2.1 `GET /api/v1/admin/tenants/`
Lists all tenants with health metrics.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "count": 45,
    "results": [
      {
        "id": 1,
        "name": "National Engineering College",
        "slug": "nec",
        "tier": "PROFESSIONAL",
        "is_active": true,
        "max_concurrent_candidates": 500,
        "active_exams_count": 3,
        "registered_users_count": 2150
      }
    ]
  }
}
```

---

### 2.2 `POST /api/v1/admin/tenants/`
Creates a new tenant (institution).

**Request:**
```json
{
  "name": "City Medical College",
  "slug": "city-medical",
  "tier": "STARTER",
  "contact_email": "admin@citymedical.edu",
  "max_concurrent_candidates": 100,
  "feature_flags": ["LIVE_PROCTORING", "LIFELINES_ENGINE"]
}
```

---

### 2.3 `POST /api/v1/admin/tenants/{tenant_id}/create-designer/`
Creates a Designer (Tenant Admin) user for the specified tenant.

**Request:**
```json
{
  "username": "exam.director",
  "email": "director@citymedical.edu",
  "first_name": "Dr. Sarah",
  "last_name": "Khan",
  "password": "TempPass2026!"
}
```

**Response `201 Created`:**
```json
{
  "status": "success",
  "data": {
    "user_id": 1001,
    "username": "exam.director",
    "role": "DESIGNER",
    "tenant_slug": "city-medical"
  }
}
```

---

## 3. Designer Exam Management Endpoints (`/api/v1/exams/`)
> **Required Role:** `DESIGNER`

### 3.1 `POST /api/v1/exams/`
Create a new exam blueprint.

**Request:**
```json
{
  "title": "Advanced Database Systems — Final Exam",
  "code": "CS-401-2026",
  "duration_minutes": 120,
  "start_time": "2026-09-01T09:00:00Z",
  "end_time": "2026-09-01T12:00:00Z",
  "total_marks": 100,
  "passing_percentage": 50,
  "shuffle_questions": true,
  "shuffle_options": true,
  "fullscreen_required": true,
  "max_tab_violations": 3,
  "instructions": "Attempt all questions. Section A is compulsory.",
  "rules": "No electronic devices. Fullscreen is mandatory."
}
```

---

### 3.2 `POST /api/v1/exams/{exam_id}/roster/import/`
Upload a CSV file to bulk-import participant roster.

**Request:** `multipart/form-data` with field `file` (CSV).
**CSV Format:** `registration_number,first_name,last_name,email`

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "imported": 298,
    "skipped_duplicates": 2,
    "errors": []
  }
}
```

---

### 3.3 `POST /api/v1/exams/{exam_id}/publish-results/`
Publishes exam results to participants.

**Request:**
```json
{
  "show_grader_feedback": true
}
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "published_at": "2026-09-05T10:00:00Z",
    "notified_participants_count": 298
  }
}
```

---

## 4. Candidate Examination Engine Endpoints (`/api/v1/attempts/`)
> **Required Role:** `PARTICIPANT`

### 4.1 `GET /api/v1/exams/{exam_id}/lobby/`
Fetches pre-exam instructions, scheduling window, eligibility, and lifelines.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "exam_id": 101,
    "title": "Advanced Database Systems — Final Exam",
    "code": "CS-401-2026",
    "duration_minutes": 120,
    "total_marks": 100.0,
    "start_time": "2026-09-01T09:00:00Z",
    "end_time": "2026-09-01T12:00:00Z",
    "is_attempt_allowed": true,
    "instructions": "Attempt all questions...",
    "rules": "Fullscreen required. 3 tab switches = auto-submit.",
    "lifelines_available": [
      { "type": "SKIP_QUESTION", "name": "Skip Question", "max_allowed": 3 },
      { "type": "FIFTY_FIFTY",   "name": "50:50 Eliminator", "max_allowed": 2 }
    ],
    "attempt_status": "NOT_STARTED",
    "sections": [
      { "id": 1, "title": "Section A: MCQs", "question_count": 40, "marks_per_question": 1.0 },
      { "id": 2, "title": "Section B: Essays", "question_count": 2, "marks_per_question": 10.0 }
    ]
  }
}
```

---

### 4.2 `POST /api/v1/exams/{exam_id}/start/`
Initializes or resumes an `ExamAttempt`.

**Request:**
```json
{
  "client_resolution": "1920x1080",
  "client_user_agent": "Mozilla/5.0..."
}
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "attempt_id": 5042,
    "resume_token": "a8f9c73e91b2c4e5f6a7b8c9d0e1f2a3",
    "server_time": "2026-09-01T09:05:00Z",
    "deadline": "2026-09-01T11:05:00Z",
    "remaining_seconds": 7200,
    "bonus_minutes": 0,
    "questions": [
      {
        "id": 1201, "section_id": 1, "order": 1,
        "type": "MCQ_SINGLE", "prompt": "What is normalization?",
        "image_url": null, "points": 1.0,
        "options": [
          { "id": 401, "text": "Data organization technique", "image_url": null },
          { "id": 402, "text": "A type of join", "image_url": null },
          { "id": 403, "text": "Index creation", "image_url": null },
          { "id": 404, "text": "Query optimization", "image_url": null }
        ],
        "saved_selected_options": [],
        "saved_text_response": null,
        "is_bookmarked": false,
        "is_skipped": false
      }
    ]
  }
}
```

---

### 4.3 `POST /api/v1/attempts/{attempt_id}/heartbeat/`
Auto-save answers every 15 seconds and sync server state.

**Request:**
```json
{
  "active_question_id": 1201,
  "answers_delta": [
    {
      "question_id": 1201,
      "selected_option_ids": [401],
      "text_response": null,
      "is_bookmarked": false,
      "is_skipped": false
    }
  ]
}
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "server_time": "2026-09-01T09:20:15Z",
    "remaining_seconds": 6285,
    "bonus_minutes_awarded": 0,
    "status": "IN_PROGRESS",
    "live_broadcast": {
      "id": 5,
      "message": "Notice: Question 14 has a correction. Please re-read carefully.",
      "created_at": "2026-09-01T09:18:00Z"
    }
  }
}
```

---

### 4.4 `POST /api/v1/attempts/{attempt_id}/lifeline/`
Apply a lifeline (50:50, Skip, Hint, Bookmark).

**Request:**
```json
{ "lifeline_type": "FIFTY_FIFTY", "question_id": 1201 }
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "lifeline_type": "FIFTY_FIFTY",
    "eliminated_option_ids": [402, 404],
    "remaining_uses_for_lifeline": 1
  }
}
```

---

### 4.5 `POST /api/v1/attempts/{attempt_id}/violation/`
Log a proctoring incident.

**Request:**
```json
{ "violation_type": "TAB_BLUR", "details": "Window lost focus" }
```

**Response `200 OK`:**
```json
{
  "status": "recorded",
  "data": {
    "violation_count": 1,
    "max_allowed": 3,
    "action_triggered": "WARNING_MODAL",
    "warning_message": "⚠️ Warning 1 of 3: Leaving exam screen is prohibited."
  }
}
```

---

### 4.6 `POST /api/v1/attempts/{attempt_id}/submit/`
Finalize and submit the exam session.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "attempt_id": 5042,
    "submitted_at": "2026-09-01T11:00:12Z",
    "status": "SUBMITTED",
    "total_answered": 41,
    "total_skipped": 1,
    "confirmation_hash": "e9b4c7...f8"
  }
}
```

---

### 4.7 `GET /api/v1/participants/my-exams/`
Returns the authenticated participant's exam history.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": [
    {
      "exam_id": 101,
      "exam_title": "Advanced Database Systems — Final",
      "attempt_status": "GRADED",
      "results_published": true,
      "total_score": 82.5,
      "is_passed": true,
      "submitted_at": "2026-09-01T11:00:12Z"
    },
    {
      "exam_id": 98,
      "exam_title": "OS Midterm 2026",
      "attempt_status": "SUBMITTED",
      "results_published": false,
      "total_score": null,
      "is_passed": null,
      "submitted_at": "2026-08-15T10:05:00Z"
    }
  ]
}
```

---

## 5. Item Writer Endpoints (`/api/v1/questions/`)
> **Required Role:** `ITEM_WRITER` or `DESIGNER`

### 5.1 `POST /api/v1/questions/`
Create a new question.

**Request:**
```json
{
  "bank_id": 7,
  "question_type": "MCQ_SINGLE",
  "prompt": "Which SQL clause filters grouped results?",
  "points": 1.0,
  "negative_points": 0.25,
  "difficulty": "MEDIUM",
  "blooms_level": "REMEMBER",
  "hint_text": "Think about the order of SQL clauses.",
  "options": [
    { "option_text": "WHERE",  "is_correct": false, "order": 1 },
    { "option_text": "HAVING", "is_correct": true,  "order": 2 },
    { "option_text": "GROUP BY", "is_correct": false, "order": 3 },
    { "option_text": "ORDER BY", "is_correct": false, "order": 4 }
  ]
}
```

**Response `201 Created`:**
```json
{
  "status": "success",
  "data": {
    "question_id": 2201,
    "question_type": "MCQ_SINGLE",
    "prompt": "Which SQL clause filters grouped results?",
    "options_count": 4
  }
}
```

---

## 6. Designer Live Ops Endpoints (`/api/v1/exams/{exam_id}/live/`)
> **Required Role:** `DESIGNER`

### 6.1 `GET /api/v1/exams/{exam_id}/live-status/`
Real-time candidate matrix with heartbeat and violation data.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "exam_id": 101,
    "total_registered": 300,
    "total_in_progress": 287,
    "total_submitted": 11,
    "total_disconnected": 2,
    "candidates": [
      {
        "roster_index": 1,
        "registration_number": "STU-2026-091",
        "full_name": "Ali Hassan",
        "attempt_id": 5042,
        "status": "IN_PROGRESS",
        "current_question_index": 24,
        "questions_answered": 23,
        "violation_count": 1,
        "last_heartbeat_seconds_ago": 8,
        "is_online": true,
        "remaining_seconds": 6285
      }
    ]
  }
}
```

---

### 6.2 `POST /api/v1/exams/{exam_id}/add-time/`
Grant bonus time to all or a specific candidate.

**Request:**
```json
{
  "target_type": "ALL",
  "target_user_id": null,
  "bonus_minutes": 10,
  "reason": "Network interruption grace period"
}
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": { "affected_candidates_count": 287, "bonus_minutes_added": 10 }
}
```

---

### 6.3 `POST /api/v1/exams/{exam_id}/broadcast/`
Send a live message to all active exam cockpits.

**Request:**
```json
{
  "message": "Notice: Question 14 refers to the 2024 schema, not 2026.",
  "expires_in_minutes": 10
}
```

---

## 7. Grader Evaluation Endpoints (`/api/v1/grading/`)
> **Required Role:** `GRADER`

### 7.1 `GET /api/v1/grading/allocations/`
Lists all active grading batches assigned to the authenticated grader.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": [
    {
      "allocation_id": 12,
      "exam_title": "Advanced Database Systems — Final",
      "candidate_range": "001–100",
      "total_attempts": 98,
      "marked_count": 45,
      "draft_count": 10,
      "pending_count": 43,
      "completion_percentage": 55.1,
      "deadline": "2026-09-03T23:59:00Z",
      "status": "IN_PROGRESS"
    }
  ]
}
```

---

### 7.2 `POST /api/v1/grading/answers/{answer_id}/score/`
Score a candidate's subjective response.

**Request:**
```json
{
  "marks_awarded": 8.5,
  "rubric_breakdown": {
    "crit_1_conceptual_clarity": 4.5,
    "crit_2_working_steps": 4.0
  },
  "grader_notes": "Correct approach with minor formula error.",
  "feedback_to_student": "Good systematic approach. Review normalization forms.",
  "is_draft": false
}
```

---

## 8. Bulk Data Import Endpoints (`/api/v1/imports/`)
> **Required Role:** `DESIGNER`, `ITEM_WRITER`, or `SUPER_ADMIN`

### 8.1 `GET /api/v1/imports/templates/{import_type}/`
Downloads the official formatted sample template file with instructions and sample rows.

**Path Parameters:**
* `import_type`: `PARTICIPANT_ROSTER`, `QUESTION_BANK`, `FACULTY_USERS`, `EXAM_BLUEPRINT`

**Query Parameters:**
* `format`: `csv` (default) or `xlsx`

**Response `200 OK`:** File stream (`Content-Disposition: attachment; filename="sample_question_bank_template.xlsx"`)

---

### 8.2 `POST /api/v1/imports/validate/`
Performs dry-run schema validation on an uploaded file without modifying the database.

**Request:** `multipart/form-data`
* `import_type`: `QUESTION_BANK`
* `target_id`: `12` (Bank ID or Exam ID)
* `file`: `questions_upload.xlsx` (or `.zip` with diagrams)

**Response `200 OK` (Validation Passed):**
```json
{
  "status": "success",
  "data": {
    "job_id": 84,
    "status": "PREVIEW_READY",
    "total_rows": 150,
    "valid_rows_count": 150,
    "error_count": 0,
    "preview_rows": [
      {
        "row_number": 1,
        "question_type": "MCQ_SINGLE",
        "prompt": "Evaluate the integral of cos(x) dx.",
        "points": 2.0,
        "difficulty": "EASY",
        "options": ["sin(x) + C", "-sin(x) + C", "tan(x) + C", "cos(x) + C"],
        "correct_option": "1"
      }
    ],
    "message": "All 150 rows validated successfully. Ready for commit."
  }
}
```

**Response `422 Unprocessable Entity` (Validation Errors Found):**
```json
{
  "status": "error",
  "code": "VALIDATION_FAILED",
  "data": {
    "total_rows": 50,
    "error_count": 3,
    "errors": [
      {
        "row_number": 4,
        "field": "correct_options",
        "received_value": "5",
        "error_message": "Index '5' out of range. Question only provides 4 options."
      },
      {
        "row_number": 12,
        "field": "points",
        "received_value": "-2.0",
        "error_message": "Question points must be a positive decimal."
      }
    ]
  }
}
```

---

### 8.3 `POST /api/v1/imports/commit/`
Executes atomic database ingestion for a validated `DataImportJob`.

**Request Body:**
```json
{
  "job_id": 84,
  "overwrite_existing": false
}
```

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "job_id": 84,
    "status": "COMPLETED",
    "total_ingested": 150,
    "failed_count": 0,
    "completed_at": "2026-09-01T10:15:22Z"
  }
}
```

---

### 8.4 `GET /api/v1/imports/jobs/{job_id}/`
Tracks background import job status and retrieves error audit logs.

**Response `200 OK`:**
```json
{
  "status": "success",
  "data": {
    "job_id": 84,
    "import_type": "PARTICIPANT_ROSTER",
    "status": "COMPLETED",
    "total_rows": 500,
    "processed_rows": 500,
    "successful_rows": 498,
    "failed_rows": 2,
    "error_log": [
      {"row": 142, "field": "email", "error": "Duplicate candidate registration STU-2026-142 skipped."}
    ],
    "created_at": "2026-09-01T10:14:00Z",
    "completed_at": "2026-09-01T10:14:15Z"
  }
}
```

