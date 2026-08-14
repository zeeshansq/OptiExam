# REST API Specification — OptiExam Live Examination & Grading API
**Document Version:** 1.0.0  
**Base URL:** `/api/v1/`  
**Authentication:** Session Authentication / Token Bearer / Custom Exam Session Nonce  
**Headers Required:**
* `Content-Type: application/json`
* `X-Tenant-Slug: <tenant_slug>`
* `X-CSRFToken: <csrf_token>` (for session auth)

---

## 1. Candidate Examination Engine Endpoints

### 1.1 `GET /api/v1/exams/{exam_id}/lobby/`
Fetches pre-exam instructions, scheduling window, candidate eligibility, and allowed lifelines before attempt start.

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "exam_id": 101,
    "title": "Advanced Engineering Mathematics - Midterm",
    "code": "ENG-MATH-301",
    "duration_minutes": 90,
    "total_marks": 100.0,
    "start_time": "2026-09-01T09:00:00Z",
    "end_time": "2026-09-01T12:00:00Z",
    "is_attempt_allowed": true,
    "instructions": "All questions in Section A are compulsory...",
    "rules": "Fullscreen required. 3 tab switches will result in auto-submission.",
    "lifelines_available": [
      {
        "type": "SKIP_QUESTION",
        "name": "Skip Question Quota",
        "max_allowed": 3
      },
      {
        "type": "FIFTY_FIFTY",
        "name": "50:50 Eliminator",
        "max_allowed": 2
      }
    ],
    "attempt_status": "NOT_STARTED"
  }
}
```

---

### 1.2 `POST /api/v1/exams/{exam_id}/start/`
Initializes a new `ExamAttempt` or securely resumes an active attempt.

#### Request Body:
```json
{
  "client_resolution": "1920x1080",
  "client_user_agent": "Mozilla/5.0..."
}
```

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "attempt_id": 5042,
    "resume_token": "a8f9c73e91b2c4e5f6a7b8c9d0e1f2a3",
    "server_time": "2026-09-01T09:05:00Z",
    "started_at": "2026-09-01T09:05:00Z",
    "deadline": "2026-09-01T10:35:00Z",
    "remaining_seconds": 5400,
    "bonus_minutes": 0,
    "questions": [
      {
        "id": 1201,
        "section_id": 1,
        "order": 1,
        "type": "MCQ_SINGLE",
        "prompt": "Evaluate the definite integral of sin(x) from 0 to pi.",
        "image_url": null,
        "points": 2.0,
        "options": [
          {"id": 401, "text": "0", "image_url": null},
          {"id": 402, "text": "1", "image_url": null},
          {"id": 403, "text": "2", "image_url": null},
          {"id": 404, "text": "-2", "image_url": null}
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

### 1.3 `POST /api/v1/attempts/{attempt_id}/heartbeat/`
Sent automatically by the client every 15 seconds to auto-save candidate answers, sync server time, and poll for live supervisor announcements or time extensions.

#### Request Body:
```json
{
  "active_question_id": 1201,
  "answers_delta": [
    {
      "question_id": 1201,
      "selected_option_ids": [403],
      "text_response": null,
      "is_bookmarked": false,
      "is_skipped": false
    }
  ]
}
```

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "server_time": "2026-09-01T09:20:15Z",
    "remaining_seconds": 4485,
    "bonus_minutes_awarded": 0,
    "status": "IN_PROGRESS",
    "live_broadcast": null
  }
}
```

---

### 1.4 `POST /api/v1/attempts/{attempt_id}/lifeline/`
Applies a lifeline (e.g. 50:50 or Skip Question).

#### Request Body:
```json
{
  "lifeline_type": "FIFTY_FIFTY",
  "question_id": 1201
}
```

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "lifeline_type": "FIFTY_FIFTY",
    "question_id": 1201,
    "eliminated_option_ids": [401, 404],
    "remaining_uses_for_lifeline": 1
  }
}
```

---

### 1.5 `POST /api/v1/attempts/{attempt_id}/violation/`
Logs a proctoring incident (e.g. tab blur or fullscreen escape).

#### Request Body:
```json
{
  "violation_type": "TAB_BLUR",
  "details": "Candidate switched to an external window"
}
```

#### Response `200 OK`:
```json
{
  "status": "recorded",
  "data": {
    "violation_count": 1,
    "max_allowed": 3,
    "action_triggered": "WARNING_MODAL",
    "warning_message": "Warning 1 of 3: Leaving the exam screen is strictly prohibited."
  }
}
```

---

### 1.6 `POST /api/v1/attempts/{attempt_id}/submit/`
Finalizes the candidate's examination session.

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "attempt_id": 5042,
    "submitted_at": "2026-09-01T10:30:12Z",
    "status": "SUBMITTED",
    "total_answered": 48,
    "total_skipped": 2,
    "confirmation_hash": "e9b4c7...f8"
  }
}
```

---

## 2. Designer Live Ops Control Room Endpoints

### 2.1 `GET /api/v1/exams/{exam_id}/live-status/`
Provides real-time candidate statuses, heartbeats, and proctoring metrics.

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "exam_id": 101,
    "total_registered": 250,
    "total_in_progress": 238,
    "total_submitted": 10,
    "total_disconnected": 2,
    "candidates": [
      {
        "user_id": 842,
        "registration_number": "STU-2026-091",
        "full_name": "Ali Hassan",
        "attempt_id": 5042,
        "status": "IN_PROGRESS",
        "current_question_index": 24,
        "questions_answered": 23,
        "violations_count": 1,
        "last_heartbeat_seconds_ago": 4,
        "is_online": true
      }
    ]
  }
}
```

---

### 2.2 `POST /api/v1/exams/{exam_id}/add-time/`
Grants live extra time to active candidates.

#### Request Body:
```json
{
  "target_type": "ALL",
  "target_user_id": null,
  "bonus_minutes": 10,
  "reason": "Server network maintenance grace period"
}
```

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "affected_candidates_count": 238,
    "bonus_minutes_added": 10
  }
}
```

---

## 3. Grader Evaluation Endpoints

### 3.1 `POST /api/v1/grading/answers/{answer_id}/score/`
Scores a candidate's subjective essay or short answer.

#### Request Body:
```json
{
  "marks_awarded": 8.5,
  "rubric_breakdown": {
    "crit_1_conceptual_clarity": 4.5,
    "crit_2_working_steps": 4.0
  },
  "grader_notes": "Well explained with correct formula.",
  "feedback_to_student": "Good work on step 3 derivation.",
  "is_draft": false
}
```

#### Response `200 OK`:
```json
{
  "status": "success",
  "data": {
    "answer_id": 12049,
    "marks_awarded": 8.5,
    "is_draft": false,
    "evaluated_at": "2026-09-02T14:22:00Z"
  }
}
```
