# Phase 3: Live Examination Engine, Anti-Cheating & Control Room
**Document:** `Doc/phase_03_live_exam_engine_and_proctoring.md`  
**Project:** OptiExam Assessment Platform  
**Target Environment:** Python 3.12+ / Django 5.x / `C:\venv\envoptiexam`  
**Document Version:** 1.0.0  
**Phase Status:** Ready for Implementation (Depends on Phases 1 & 2)  

---

## 1. Phase Overview & Strategic Objectives

Phase 3 implements the high-stakes execution core of OptiExam. It delivers the **Participant Exam Lobby**, the **Lockdown Anti-Cheating Examination Cockpit** (with DOM event shields, fullscreen enforcement, tab-switch detection, and 15-second heartbeat auto-save), the **Resilient Crash Recovery Engine** (zero data loss on power outage or browser crash), the **Lifeline Engine** (50:50, Skip, Hint, Bookmark), and the **Designer Live Ops Command Center** (real-time candidate monitoring, dynamic time extensions, and live broadcast alerts).

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PHASE 3 DELIVERABLES                          │
├────────────────────────────────────────────────────────────────────────┤
│  1. Participant Exam Lobby with Live Countdown & Pre-Exam Instructions │
│  2. Attempt Initialization Service with Deterministic Seed Shuffling   │
│  3. Distraction-Free Lockdown Cockpit UI (`base_exam_cockpit.html`)   │
│  4. DOM Anti-Cheating Event Shields (Copy/Paste/Key/Inspect Lock)      │
│  5. 15-Second Heartbeat Worker with Server-Authoritative Time Sync     │
│  6. Resilient LocalStorage Offline Queue & Crash/Reboot Auto-Resume   │
│  7. Interactive Question Palette Matrix (Status Colors & Navigation)   │
│  8. Lifeline Execution Engine (50:50 Eliminator, Skip Quota, Hints)    │
│  9. Designer Live Ops Control Room (Candidate Matrix, +Time, Broadcast)│
│  10. Background `auto_submit_expired` Management Command               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Target Component & Directory Layout

```
apps/
├── submissions/
│   ├── models.py              # ExamAttempt, AttemptAnswer, ProctoringLog, AttemptLifelineUsage
│   ├── admin.py
│   ├── urls.py                # app_name = 'submissions'
│   ├── views/
│   │   ├── lobby_views.py     # Candidate lobby & countdown screen
│   │   ├── cockpit_views.py   # Fullscreen exam cockpit view
│   │   └── api_views.py       # Heartbeat, lifeline, violation, submit endpoints
│   ├── services/
│   │   ├── attempt_service.py # initialize_attempt, resume_attempt, seed_shuffler
│   │   ├── heartbeat_service.py # process_heartbeat, auto_save_answers
│   │   ├── lifeline_service.py # execute_lifeline (50:50, skip, hint)
│   │   ├── proctoring_service.py # log_violation, evaluate_auto_submit
│   │   └── submission_service.py # finalize_submission, auto_submit_expired
│   ├── selectors/
│   │   └── attempt_selectors.py # get_candidate_active_attempt, get_attempt_state
│   ├── management/
│   │   └── commands/
│   │       └── auto_submit_expired.py # Cron/scheduled command
│   ├── templates/submissions/
│   │   ├── exam_lobby.html    # Pre-exam instructions, countdown, start button
│   │   ├── exam_cockpit.html  # Live examination screen
│   │   └── submission_receipt.html # Post-submission confirmation receipt
│   └── tests/
├── notifications/
│   ├── models.py              # Notification, BroadcastAlert
│   ├── services/
│   │   └── notification_service.py # dispatch_exam_alert, dispatch_broadcast
│   └── tests/
└── exams/
    ├── views/
    │   └── live_ops_views.py  # Designer real-time exam command center
    ├── services/
    │   └── live_ops_service.py # grant_bonus_time, send_broadcast, force_controls
    └── templates/exams/
        └── live_ops.html      # Real-time candidate matrix & ops toolbar
static/
├── css/
│   └── cockpit.css            # Distraction-free, high-contrast examination UI
└── js/
    ├── anti-cheat-shield.js   # Fullscreen, clipboard, keypress, visibility shields
    ├── heartbeat-sync.js      # 15s auto-save sync, offline queue, server clock
    ├── exam-cockpit.js        # Question navigation, palette status, answer handlers
    ├── lifeline-engine.js     # 50:50 strikeout, skip question, hint modal
    └── live-ops.js            # Designer live candidate matrix polling & actions
```

---

## 3. Step-by-Step Implementation Tasks

### Task 3.1: Participant Exam Lobby (`apps/submissions`)
1. Build `ExamLobbyView` at `/{tenant_slug}/exam/{exam_id}/lobby/`:
   * Displays title, code, duration, total marks, sections summary, and allowed lifelines.
   * Renders the complete instructions and anti-cheating conduct rules authored by Designer.
   * Real-time JS countdown timer to `exam.start_time`.
   * The **"Start Exam"** button remains disabled until `now() >= exam.start_time` OR `exam.is_force_enabled == True`.
   * Verifies candidate exists in `ExamParticipantRoster` before allowing start.

### Task 3.2: Attempt Initialization & Seeded Shuffling
1. Implement `initialize_attempt(exam, participant, client_meta)` in `attempt_service.py`:
   * Checks for existing `ExamAttempt`. If already `IN_PROGRESS`, triggers resume flow.
   * Generates a unique 64-character `resume_token`.
   * Computes deterministic integer seed: `candidate_seed = hash(f"{participant.id}_{exam.id}")`.
   * Pre-creates blank `AttemptAnswer` records for all assigned questions.
   * If `exam.shuffle_questions == True`, question order is randomized per candidate seed.
   * If `exam.shuffle_options == True`, MCQ option order is randomized per candidate seed.
   * Sets `started_at = timezone.now()` and status to `IN_PROGRESS`.
   * Wrapped in `@transaction.atomic`.

### Task 3.3: Distraction-Free Exam Cockpit UI
1. Create `templates/base_exam_cockpit.html` and `static/css/cockpit.css`:
   * Clean, high-contrast, distraction-free top bar: Exam Title, Question Palette trigger, Live Countdown Timer Pill, Active Lifelines bar, "Submit Exam" button.
   * Main Content: Question prompt, high-res diagram with local zoom modal, answer input area tailored to question type.
   * Bottom Action Bar: Previous Question, Next Question, Clear Response, Bookmark for Review, Lifelines Action dropdown.
2. Build native question input components for all 5 formats:
   * `MCQ_SINGLE`: Radio buttons with custom styled option cards.
   * `MCQ_MULTIPLE`: Checkboxes with multi-select highlight.
   * `IMAGE_MCQ`: Image diagram container with click-to-zoom and option selector.
   * `SHORT_ANSWER`: Textarea with dynamic live word-counter and word-limit warning.
   * `LONG_ESSAY`: Structured essay editor with auto-expanding textarea.

### Task 3.4: Anti-Cheating Event Shields (`static/js/anti-cheat-shield.js`)
1. **Fullscreen Enforcement**:
   * Auto-requests native `document.documentElement.requestFullscreen()` on exam start.
   * Listens to `fullscreenchange`. Exiting fullscreen triggers a modal alert with a 15-second grace countdown to return to fullscreen.
   * Each unexcused exit increments `violation_count` and logs `FULLSCREEN_EXIT`.
2. **DOM Event Shielding**:
   * Block `contextmenu` (right-click).
   * Block `copy`, `cut`, `paste`, `selectstart` (text selection), and `dragstart`.
   * Intercept keyboard shortcuts: `Ctrl+C`, `Ctrl+V`, `Ctrl+P`, `Ctrl+U`, `F12`, `Alt+Tab`, `PrintScreen`.
3. **Visibility & Focus Monitoring**:
   * Listens to `visibilitychange` and `window.onblur`.
   * Window loss of focus increments `violation_count` and logs `TAB_BLUR`.
4. **Violation Escalation**:
   * On reaching `exam.max_tab_violations`, triggers automatic submission with reason `AUTO_SUBMITTED`.

### Task 3.5: Heartbeat Sync & Resilient Auto-Save (`static/js/heartbeat-sync.js`)
1. Client background worker fires every 15 seconds:
   * POST payload: `{active_question_id: 101, answers_delta: [{question_id: 101, selected_option_ids: [4], text_response: null, ...}]}`.
   * Server upserts `AttemptAnswer` records and returns:
     ```json
     {
       "status": "success",
       "data": {
         "server_time": "2026-09-01T09:20:15Z",
         "remaining_seconds": 4485,
         "bonus_minutes_awarded": 0,
         "live_broadcast": null
       }
     }
     ```
2. **Server-Authoritative Clock**: The client timer synchronizes to `data.remaining_seconds` on every heartbeat, neutralizing local clock tampering.
3. **Encrypted Local Storage Queue & Crash Recovery**:
   * On any answer change, response is immediately written to browser `localStorage` encrypted with `EXAM_RESUME_AES_SECRET`.
   * If network fails, non-blocking amber indicator appears: *"Offline: Saved Locally"*.
   * If browser crashes or computer turns off, re-opening the exam URL restores the exact remaining time, active question, and all saved answers seamlessly.

### Task 3.6: Lifeline Execution Engine
1. Implement `execute_lifeline(attempt, lifeline_type, question_id)` in `lifeline_service.py`:
   * **`FIFTY_FIFTY`**: Validates question is 4-option MCQ, identifies 2 incorrect options, records usage in `AttemptLifelineUsage`, returns eliminated option IDs. Client strikes through and disables those 2 options.
   * **`SKIP_QUESTION`**: Marks `AttemptAnswer.is_skipped = True`, decrements remaining skip quota.
   * **`HINT_TOKEN`**: Retrieves `Question.hint_text`, returns hint text, records usage.
   * **`BOOKMARK_FLAG`**: Sets `AttemptAnswer.is_bookmarked = True`, updates palette color.

### Task 3.7: Question Palette & Submission Confirmation
1. Interactive Question Palette Matrix:
   * Dot/tile grid with color coding:
     * **Grey**: Not visited
     * **Blue**: Visited / Current
     * **Green**: Answered
     * **Amber**: Bookmarked for review
     * **Red**: Skipped
   * Allows 1-click jump to any question (if `allow_back_navigation == True`).
2. Final Submission Workflow:
   * Candidate clicks "Submit Exam".
   * Modal dialog shows complete breakdown: Total Answered, Total Unanswered, Total Skipped, Total Bookmarked.
   * User enters confirmation prompt → POST to `/api/v1/attempts/{id}/submit/`.
   * Server marks status `SUBMITTED`, locks all answer records, and renders `submission_receipt.html`.

### Task 3.8: Designer Live Ops Control Room (`apps/exams`)
1. Build `LiveOpsView` at `/{tenant_slug}/exams/{exam_id}/live/`:
   * Real-time candidate matrix polling every 5 seconds via REST API:
     * Candidate avatar, name, registration #, current question, answered count, heartbeat status (Green = Active < 30s, Red = Disconnected > 60s), violation count.
2. **Dynamic Bonus Time Extender**:
   * Designer selects `+5`, `+10`, `+15`, or custom minutes for ALL candidates or a single student.
   * Updates `ExamAttempt.bonus_minutes_awarded`. Candidate cockpits smoothly receive the extra time on next heartbeat with an in-app toast banner.
3. **Live Broadcast Dispatcher**:
   * Designer inputs announcement message (e.g. *"Notice: Question 14 typo corrected"*).
   * Creates `BroadcastAlert` record. Displayed in candidate cockpits within 15 seconds.
4. **Emergency Force Controls**:
   * Force Start: Immediately enables exam for candidates who missed schedule start.
   * Force Submit: Submits candidate attempt in case of lab emergency.

### Task 3.9: Background Task: `auto_submit_expired`
1. Author Django management command `apps/submissions/management/commands/auto_submit_expired.py`.
2. Queries all `ExamAttempt` records where `status == IN_PROGRESS` and `started_at + duration + bonus_time < now()`.
3. Marks them `AUTO_SUBMITTED`, updates `submitted_at = now()`, and logs audit entry.

### Task 3.10: Candidate Dry-Run Simulation Studio (`apps/submissions` & `apps/exams`)
1. **Interactive Candidate Sandbox Route:** `/{tenant_slug}/exams/{exam_id}/dry-run/`:
   * Allows Designers (Tenant Admins) and authorized Item Writers to execute a full interactive dry run of the examination.
   * Runs the exact same `exam_cockpit.html` interface, CSS, anti-cheat shields, timer, and question layouts that students experience.
2. **Simulation Environment Isolation:**
   * Creates an isolated simulation attempt with `is_simulation = True`.
   * Completely excluded from official student rosters, grading queues, audit logs, and result statistics.
3. **Interactive Simulation Controls:**
   * **Simulation Floating Banner:** Non-intrusive top-right banner identifying `"DRY-RUN SIMULATION MODE"` with quick exit button.
   * **Test Anti-Cheat Toggle:** Test fullscreen lock, tab-blur warnings, and clipboard intercept in safe sandbox mode.
   * **Test Lifelines:** Execute 50:50 strikes, hints, and bookmark flags live.
   * **1-Click Reset / Re-Shuffle:** Button to clear the simulation attempt and re-seed question/option shuffle to test different student variations.
4. **Item Writer Access Control:**
   * Automatically allows Item Writers to run simulations for exams that contain questions from their authorized question banks or where they are assigned.


---

## 4. Anti-Cheating & Exam Lifecycle State Machine

```
              ┌─────────────────────────────────────────┐
              │           Candidate in Lobby            │
              └────────────────────┬────────────────────┘
                                   │ "Start Exam" (Roster verified)
                                   ▼
              ┌─────────────────────────────────────────┐
              │          Attempt: IN_PROGRESS           │
              │  - Fullscreen Lock active               │
              │  - DOM Event Shields active             │
              │  - 15s Heartbeat Auto-Save cycle        │
              └────────┬───────────┬───────────┬────────┘
                       │           │           │
      Tab Blur / Exit  │           │ Timeout   │ Candidate Clicks Submit
      Violations ≥ Max │           │ Expired   │
                       ▼           ▼           ▼
              ┌─────────────────────────────────────────┐
              │    Attempt: SUBMITTED / AUTO_SUBMITTED  │
              │  - Inputs locked                        │
              │  - Trigger Auto-Scoring Engine (MCQ)    │
              │  - Render Submission Receipt            │
              └─────────────────────────────────────────┘
```

---

### 4.1 UI/UX Cockpit & Live Ops Matrix (Whole-Project Standards Enforced)
1. **Edge-to-Edge Candidate Cockpit**:
   * Uses 100% full screen width (`width: 100vw; height: 100vh;`) under browser fullscreen lockdown.
   * Left Question Navigator drawer (fluid 260px) + Expansive 100% fluid Question Response Area + Fixed Persistent Timer bar at top.
2. **Live Ops Control Room (Designer)**:
   * 100% full screen width candidate monitoring matrix displaying hundreds of concurrent candidates in high-density grid.
   * **Single-Line Filter Toolbar:** Filter by student name, registration number, live status (Active/Warning/Offline), with `[Filter]` button and `[Clear]` icon button (`rotate-ccw`) in one line (`.filter-row-single`).
   * **Icon-Only Action Buttons with Concise Tooltips:**
     - **Grant +5m Bonus:** `.action-btn-success` with `{% icon 'clock' %}` and `data-tooltip="Bonus +5m"`
     - **Inspect Live Proctoring Feed:** `.action-btn-inspect` with `{% icon 'eye' %}` and `data-tooltip="Inspect"`
     - **Force Submit Attempt:** `.action-btn-delete` with `{% icon 'trash-2' %}` and `data-tooltip="Force Submit"`


---


## 5. Verification & Automated Test Plan

### Test Suite Execution
```powershell
& "C:\venv\envoptiexam\Scripts\python.exe" -m pytest apps/submissions/tests -v --cov=apps/submissions
```

### Key Test Cases:
1. `test_attempt_initialization_seed_determinism`: Validates candidate A and candidate B receive different randomized question orders under identical exam blueprint.
2. `test_heartbeat_answers_delta_upsert`: Validates answers are persisted accurately on 15s heartbeat payload.
3. `test_server_authoritative_timer_calculation`: Verifies client attempting to alter timestamp cannot extend remaining exam time.
4. `test_50_50_lifeline_eliminates_two_wrong_options`: Validates 50:50 returns exactly 2 incorrect options and cannot be used beyond max allowed quota.
5. `test_violation_escalation_auto_submission`: Validates that on 3rd tab switch, status changes to `AUTO_SUBMITTED` and inputs are locked.
6. `test_crash_recovery_state_restoration`: Simulates browser crash and validates reopening attempt URL restores all saved answers and correct remaining time.
7. `test_live_ops_bonus_time_grant`: Validates Designer granting `+10` minutes increases `remaining_seconds` on candidate heartbeat response.

---

## 6. Definition of Done (DoD) for Phase 3
* [ ] Candidates can enter lobby, review rules, and start exam on schedule.
* [ ] Fullscreen lockdown, clipboard lock, and tab-switch detection function seamlessly.
* [ ] Answers auto-save every 15 seconds; browser crashes recover without data loss.
* [ ] Lifelines (50:50, Skip, Hint, Bookmark) execute accurately with quota enforcement.
* [ ] Designer Live Ops Control Room monitors candidates live and can inject bonus time dynamically.
* [ ] All tests pass with ≥ 90% code coverage.
