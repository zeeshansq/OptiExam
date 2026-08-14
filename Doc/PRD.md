# Product Requirements Document (PRD) — OptiExam
**Project Name:** OptiExam  
**Document Version:** 2.0.0  
**Document Status:** Approved & Baseline Specification  
**Target Framework:** Python 3.12+ / Django 5.x (PostgreSQL / SQLite dual-engine)  
**Primary Environment Path:** `C:\venv\envoptiexam`  
**System Class:** Multi-Tenant Offline-Ready High-Stakes Examination & Assessment SaaS Platform  
**Last Audited:** 2026-08-14

---

## 1. Executive Summary & Vision

### 1.1 Product Overview
**OptiExam** is a next-generation, multi-tenant examination lifecycle and assessment SaaS platform built for educational institutions (schools, colleges, universities) and corporate certification bodies. It provides end-to-end support for the entire examination workflow:

```
Authoring  →  Blueprinting & Configuration  →  Proctored Live Conduction
     →  Distributed Batched Grading  →  Result Publication & Analytics
```

### 1.2 Core Pillars

| # | Pillar | Description |
|---|---|---|
| 1 | **Multi-Tenancy with Complete Isolation** | Independent workspaces, branding, question banks, participant rosters, and role management per institution. |
| 2 | **100% Offline-Ready Asset Architecture** | Zero external CDN dependencies. All CSS, JS, fonts (Inter, Outfit, JetBrains Mono), and icons (Lucide SVG) are bundled locally. |
| 3 | **Ironclad Anti-Cheating & Proctoring** | Fullscreen enforcement, clipboard lock, developer tools block, tab-switch detection, heartbeat sync (15-second intervals), state snapshotting, and crash recovery. |
| 4 | **Dynamic Examination Engine & Lifeline Framework** | Responsive UI for 5 question types, candidate-seeded shuffling, and configurable lifelines (Skip, 50:50, Hint, Bookmark). |
| 5 | **Live Exam Ops Control Room** | Real-time exam supervision: add extra time on the fly, force-start attempts, broadcast alerts, and monitor candidate status live. |
| 6 | **Distributed Batched Grading Matrix** | Candidate batch partitioning (Candidates 1–100 → Grader A; 101–200 → Grader B), double-blind scoring, automated MCQ grading, rubric-based manual scoring, SLA tracking, and Chief Examiner moderation. |
| 7 | **Controlled Result Publication** | Designer controls exactly when results become visible to participants. Graders can view and modify their own finalized marks. Participants see results only after explicit release. |

---

## 2. User Roles, Personas & Permissions Matrix

OptiExam defines **5 distinct user tiers**, each with a custom top-navigation layout, specialized dashboard, and strict RBAC enforcement.

```
                      ┌─────────────────────────────────────────┐
                      │        SUPER ADMIN (SaaS Level)         │
                      │  Tenant Onboarding, Quotas, Global Logs │
                      └────────────────────┬────────────────────┘
                                           │ Grants Access & Manages
                      ┌────────────────────▼────────────────────┐
                      │       DESIGNER (Tenant Admin)           │
                      │  Exam Blueprint, Rules, Batches, Ops    │
                      └───────┬─────────────────────────┬───────┘
               Manages ◄──────┤                         ├──────► Assigns Graders
      ┌─────────────────────▼─────┐               ┌────▼──────────────────────┐
      │        ITEM WRITER        │               │          GRADER           │
      │ Questions, Rubrics, Media │               │ Scoring, Moderation, SLA  │
      └───────────────────────────┘               └───────────────────────────┘
                                           ▲
                                           │ Attempts Assigned Exams
                      ┌────────────────────┴────────────────────┐
                      │              PARTICIPANT                │
                      │  Lobby → Attempt → History → Results   │
                      └─────────────────────────────────────────┘
```

### 2.1 Role 1: Super Admin (SaaS Application Manager)
* **Persona:** SaaS Platform Owner / Global IT Director.
* **Access Level:** Platform-wide. No tenant restriction.
* **Core Responsibilities:**
  * Provision, suspend, or deactivate institutions (tenants).
  * Create and assign Tenant Admin (Designer) user accounts.
  * Configure tenant subscription tiers (Starter / Professional / Enterprise), concurrent candidate limits, storage quotas, and granular feature flags.
  * View global audit log stream: logins, role grants, exam starts, proctoring violations, time grants.
  * System maintenance: database engine switch, cache flush, system version update.
* **Dedicated Dashboard Modules:**
  * **SaaS Health Matrix:** Active tenants, concurrent sessions, storage utilization gauges.
  * **Tenant Directory:** Filterable list with status pills (Active / Suspended / Trial).
  * **Subscription & Quota Manager:** Tier upgrade/downgrade controls with quota sliders.
  * **Global Audit Stream:** Searchable, exportable log with role-based filtering.

### 2.2 Role 2: Designer (Tenant Administrator & Exam Architect)
* **Persona:** Dean of Examinations, Head of Academic Assessments, Exam Director.
* **Access Level:** Scoped to their own tenant. Has all Item Writer capabilities.
* **Core Responsibilities:**
  * End-to-end exam creation: Title, code, subject, duration, total marks, passing percentage, full instructions (visible in exam lobby), rules, and exam-level policy settings.
  * Section creation with custom titles, question count definitions, and per-section weightage allocation.
  * Anti-cheating policy configuration per exam (fullscreen enforcement, tab-switch limit, copy-paste lock, question/option shuffling).
  * Scheduling: Open Time, Close Time, Hard Lockdown Time, and Force-Enable toggle.
  * **Lifeline configuration:** Enable/disable and set usage limits for each lifeline type per exam.
  * **Participant Roster Management:** Import CSV lists or manually add participants to specific exams. Define access codes or open-enrollment settings.
  * **Grader Allocation Matrix:** Assign candidate index ranges (e.g., #001–#100 → Grader 1, #101–#200 → Grader 2) and set SLA deadlines. Can split by section specialization.
  * **Result Publication Control:** Explicitly release results to participants. Can release per-section or full result. Control whether feedback from graders is visible.
  * **Live Exam Ops Room:** Real-time candidate matrix, force-start, force-submit, add bonus time (+5/+10/+15/custom), live broadcast announcements.
  * **Grading Progress Monitoring:** See each grader's SLA completion percentage and send in-app reminder alerts.
* **Dedicated Dashboard Modules:**
  * **Exam Blueprint Studio:** Multi-step exam builder with live preview of weightage breakdown chart.
  * **Participant Roster Hub:** Bulk CSV import, manual add, enrollment status view.
  * **Live Exam Control Room:** Real-time command center with candidate matrix.
  * **Grader Allocation Matrix:** Drag-and-assign interface with SLA tracker.
  * **Analytics & Cohort Performance Hub:** Score distribution histogram, pass/fail ratio, per-section average.

### 2.3 Role 3: Item Writer (Subject Matter Expert)
* **Persona:** Subject Teacher, Professor, Curriculum Specialist.
* **Access Level:** Limited to question banks and exams they are explicitly authorized for by the Designer.
* **Core Responsibilities:**
  * Create, edit, version, and organize questions within authorized subject question banks.
  * Author 5 question formats with dedicated dynamic UIs:
    1. **MCQ Single Choice** — Text / Math / Code prompt, 2–6 options, mark one correct.
    2. **MCQ Multiple Choice** — Mark multiple correct options with partial/negative marking.
    3. **Picture / Diagram MCQ** — Upload high-resolution local image as question body or option, with zoom tool in exam cockpit.
    4. **Short Answer** — Set word limit, add keyword guidance for graders, provide model answer.
    5. **Long Essay / Structured** — Rich model answer, structured scoring rubric criteria (per criterion max marks, descriptions).
  * Tag questions with: Difficulty (Easy/Medium/Hard), Bloom's Taxonomy level (Remember, Understand, Apply, Analyze, Evaluate, Create), topic tags.
  * Provide hint text (revealed if candidate uses Hint Token lifeline).
  * Add post-exam review explanation per MCQ option.
* **Dedicated Dashboard Modules:**
  * **Question Bank Repository:** Searchable, filterable question list with usage stats (which exams use this question).
  * **Authoring Studio:** Dynamic multi-format question editor with live preview.
  * **Quality Review Queue:** Questions flagged by Designer or other reviewers.

### 2.4 Role 4: Grader (Evaluation & Scoring Officer)
* **Persona:** Teaching Assistant, Associate Examiner, Evaluation Board Member.
* **Access Level:** Scoped to assigned candidate batches only.
* **Core Responsibilities:**
  * Access assigned candidate batches through an anonymized queue (Double-Blind: candidate names shown as `CAND-XXXXX`).
  * Verify automated MCQ scores flagged for review (system auto-grades MCQs but grader can override with reason).
  * Score Short and Long questions using the **Split-Screen Rubric & Model Answer Cockpit**.
  * Save evaluations as `DRAFT` or finalize (`MARKED`).
  * Finalized evaluations are locked unless the Designer explicitly reopens them for modification.
  * View the history of all submissions they have evaluated with full change-audit trail.
* **Dedicated Dashboard Modules:**
  * **Assigned Batch Queue:** SLA deadline countdown, completion percentage per batch.
  * **Evaluation Cockpit:** Left pane (student submission) + Right pane (model answer + rubric matrix).
  * **Scoring Progress & SLA Tracker:** Per-question completion chart.

### 2.5 Role 5: Participant (Candidate / Student)
* **Persona:** Enrolled Student, Certification Candidate.
* **Access Level:** Scoped to their own tenant and only exams they are enrolled in.
* **Core Responsibilities:**
  * Secure login and authentication to the tenant's branded portal.
  * View **Exam Lobby** showing upcoming, active (in-progress), and completed exams with status pills.
  * Enter Exam Lobby for a specific exam: Review rules, instructions, duration, total marks, weightages, and lifelines available.
  * **Attempt button** enables automatically when the schedule window begins, or when force-enabled by the Designer.
  * Complete exam in anti-cheating cockpit: Question palette navigation, back/forward (if enabled), answer save, lifeline triggers, auto-save heartbeat, real-time countdown timer.
  * If exam window closes and attempt is in progress: auto-submission is triggered.
  * View **My Exam History** section with attempt statuses (`Submitted`, `Grading in Progress`, `Results Published`).
  * View post-exam scorecards and grader feedback **only after the Designer explicitly publishes the results**.
* **Dedicated Dashboard Modules:**
  * **Student Lobby:** Upcoming exams with countdown timers.
  * **Live Examination Cockpit:** Anti-cheating, auto-save, question palette.
  * **Results & Feedback Portal:** Scorecard, section-wise breakdown, grader feedback (when released).

---

## 3. High-Priority Functional Specifications

### 3.1 Multi-Tenancy Architecture

```
                    ┌───────────────────────────────────┐
                    │      Incoming HTTP Request        │
                    └──────────────────┬────────────────┘
                                       │
                    ┌──────────────────▼────────────────┐
                    │   TenantResolutionMiddleware       │
                    │  (slug from URL / cookie / domain) │
                    └──────────────────┬────────────────┘
                                       │ Attaches request.tenant
                    ┌──────────────────▼────────────────┐
                    │         Django View Layer          │
                    │   (All queries scoped to tenant)   │
                    └───────────────────────────────────┘
```

* **Tenant Identification:** Resolved from URL slug (`/{tenant_slug}/dashboard/`), custom domain mapping, or session cookie.
* **Data Isolation:** All tenant-scoped models enforce `tenant` FK at the queryset level via `TenantModelMixin` and custom `TenantManager`.
* **Branding:** Per-tenant logo, primary color, and institutional banner injected via `tenant_context` context processor.
* **Feature Flags:** Each tenant can have individual features enabled/disabled (e.g., `LIFELINES_ENGINE`, `DOUBLE_BLIND_GRADING`) controlled by the Super Admin.

### 3.2 100% Offline-Ready Asset Design System

**Zero External CDN Policy** — No requests to `fonts.googleapis.com`, `cdnjs.cloudflare.com`, `unpkg.com`, or any external host.

| Asset Type | Local Path | Technology |
|---|---|---|
| Typography (Body) | `static/fonts/inter/` | Inter WOFF2 (Regular, Medium, SemiBold, Bold) |
| Typography (Headings) | `static/fonts/outfit/` | Outfit WOFF2 (Medium, Bold, ExtraBold) |
| Typography (Code/Math) | `static/fonts/jetbrains-mono/` | JetBrains Mono WOFF2 |
| Icons | `static/icons/lucide-sprite.svg` | Lucide SVG Sprite (local bundle) |
| Core Styles | `static/css/optiexam-core.css` | Vanilla CSS 3 + CSS Variables |
| Theme (Dark/Light) | `static/css/optiexam-theme.css` | CSS Variables glassmorphism |
| Exam Cockpit Styles | `static/css/cockpit.css` | Distraction-free layout |
| Core JS | `static/js/optiexam-core.js` | Vanilla ES6+ modules |
| Anti-Cheat Engine | `static/js/anti-cheat-shield.js` | DOM event shields |
| Heartbeat Worker | `static/js/heartbeat-sync.js` | Fetch API + localStorage queue |

### 3.3 UI Design System Tokens

The OptiExam CSS design system uses the following canonical variables:

```css
/* optiexam-core.css — Design Token Definitions */
:root {
  /* Color Palette */
  --color-primary:       #4F46E5;   /* Royal Indigo — Primary Action */
  --color-primary-hover: #4338CA;   /* Indigo 700 */
  --color-accent:        #10B981;   /* Emerald Green — Success / Correct */
  --color-warning:       #F59E0B;   /* Amber — Caution / Offline Mode */
  --color-danger:        #EF4444;   /* Crimson — Violation / Fail */
  --color-surface:       #1E1E2E;   /* Deep Slate — Background */
  --color-surface-2:     #2A2A3E;   /* Elevated Card Surface */
  --color-glass:         rgba(255, 255, 255, 0.05); /* Glassmorphism base */
  --color-border:        rgba(255, 255, 255, 0.10);
  --color-text-primary:  #F1F5F9;   /* Slate 100 — Primary text */
  --color-text-muted:    #94A3B8;   /* Slate 400 — Secondary text */

  /* Typography */
  --font-ui:       'Inter', system-ui, sans-serif;
  --font-heading:  'Outfit', system-ui, sans-serif;
  --font-mono:     'JetBrains Mono', 'Courier New', monospace;

  /* Spacing Scale */
  --space-xs: 4px; --space-sm: 8px; --space-md: 16px;
  --space-lg: 24px; --space-xl: 32px; --space-2xl: 48px;

  /* Border Radius */
  --radius-sm: 6px; --radius-md: 12px; --radius-lg: 20px; --radius-full: 9999px;

  /* Shadows */
  --shadow-card:  0 4px 24px rgba(0, 0, 0, 0.3);
  --shadow-hover: 0 8px 32px rgba(79, 70, 229, 0.25);

  /* Transitions */
  --transition-fast:   150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow:   400ms ease;
}
```

### 3.4 Top Navigation Bar Specification

The top-nav is the primary UI chrome for all logged-in roles. It must contain (left to right):

1. **Tenant Logo + Brand Name** (links to role dashboard)
2. **Active Exam Resume Pill** (pulsing amber, for participants with `IN_PROGRESS` attempt)
3. *(Spacer)*
4. **Fullscreen Toggle Icon** (Lucide `maximize` / `minimize`)
5. **Notification Bell** (Lucide `bell`, red badge with unread count)
6. **Dark/Light Theme Toggle** (Lucide `moon` / `sun`)
7. **User Avatar / Name + Role Tag + Dropdown** (profile, settings, logout)

---

## 4. Examination Cockpit & Anti-Cheating Suite

### 4.1 Anti-Cheating Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                  PARTICIPANT BROWSER RUNTIME                       │
├────────────────────────────────────────────────────────────────────┤
│  ✅ Fullscreen API Lock     → Auto-enters on attempt start         │
│  🚫 DOM Event Shield        → Disable right-click, copy, paste     │
│  👁 Visibility Monitor      → Tab switch / blur detection          │
│  💓 Heartbeat Sync (15s)    → Auto-save to server + localStorage   │
│  ⏱ Timer Authority (Server) → Remaining time is server-calculated  │
│  🔐 AES Encrypted Cache     → Offline answer queue in localStorage │
└────────────────────────────┬───────────────────────────────────────┘
                             │ Periodic Sync + Violation Log
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                     OPTIEXAM SERVER ENGINE                         │
├────────────────────────────────────────────────────────────────────┤
│  • Verify Session Token & Exam Nonce                               │
│  • Record ProctoringLog events                                     │
│  • Check & Broadcast Live Events (time grants, announcements)      │
│  • Upsert AttemptAnswers (auto-save)                               │
│  • Enforce Violation Escalation (n violations → auto-submit)       │
└────────────────────────────────────────────────────────────────────┘
```

#### Anti-Cheating Feature Specifications:

| Feature | Mechanism | Configuration |
|---|---|---|
| **Fullscreen Lock** | Browser Fullscreen API, 15s grace to re-enter | Max exits configurable by Designer |
| **Clipboard Block** | `copy`, `cut`, `paste`, `selectstart`, `dragstart` events disabled | Always enforced when fullscreen required |
| **Key Shield** | `Ctrl+C/V/P/U`, `F12`, `Alt+Tab`, `PrintScreen` intercepted | Always enforced |
| **Tab/Blur Monitor** | `document.visibilitychange` + `window.onblur` | Max violations configurable (default: 3) |
| **Heartbeat** | Fetch API every 15s, exponential backoff on failure | Interval configurable in `.env` |
| **Crash Recovery** | `localStorage` AES-encrypted queue flushed on reconnect | Automatic, no config needed |
| **Seeded Shuffle** | `deterministic_shuffle(seed=hash(candidate_id + exam_id))` | Toggled per-exam by Designer |

### 4.2 Question Navigation Palette
* Candidates see a dot/tile grid of all question numbers.
* Color codes: **Grey** = Not visited, **Blue** = Visited, **Green** = Answered, **Amber** = Bookmarked, **Red** = Skipped.
* Navigation is forward-only or bidirectional based on Designer's `allow_back_navigation` flag.
* A **Summary Panel** before submission shows answered/unanswered/skipped totals and prompts confirmation.

---

## 5. Lifeline Engine Specification

| Lifeline Name | Code | Description | Configuration |
|---|---|---|---|
| **Skip Question Quota** | `SKIP_QUESTION` | Skip question without penalty. | Max skip count (e.g., 3). |
| **50:50 Eliminator** | `FIFTY_FIFTY` | Removes 2 incorrect MCQ options. | Max uses per exam (e.g., 2). |
| **Hint / Guidance Token** | `HINT_TOKEN` | Reveals Item Writer's curated hint. | Max uses per exam/section. |
| **Bookmark & Revisit** | `BOOKMARK_FLAG` | Color-tags question on navigation palette. | Unlimited (enabled by default). |

> All lifelines are configured per exam via `ExamLifelineConfig`. Candidate usage is tracked in `AttemptLifelineUsage`.

---

## 6. Live Exam Operations Control Room

The Designer's real-time command center during a live exam:

1. **Live Candidate Matrix:** Avatar, name, registration, current question, answered count, heartbeat status (Online/Disconnected), violation counter, and submission state.
2. **Dynamic Time Extender:** Add `+5`, `+10`, `+15`, or custom minutes to ALL candidates or a single selected candidate. The candidate's cockpit timer increments with a non-intrusive toast notification.
3. **Live Broadcast Dispatcher:** Instant banner alerts pushed to all active cockpits (e.g., *"Notice: Ignore Question 14"*).
4. **Emergency Force Controls:** Force-start or force-submit individual or all candidate sessions.
5. **Disconnected Candidate Alert:** If heartbeat is missing for > 60 seconds, the candidate row turns red in the matrix.

---

## 7. Participant Roster & Access Control

The Designer must define who can attempt an exam:
1. **CSV Import:** Upload a structured CSV (`registration_number, full_name, email`) to populate `ExamParticipantRoster`.
2. **Manual Entry:** Add individual participants one by one.
3. **Access Validation:** When a participant clicks "Start Exam", the server verifies they exist in `ExamParticipantRoster` for that exam and tenant. Unauthorized users see an access-denied screen.
4. **Enrollment Cutoff:** Designer can lock the roster after a defined time.

---

## 8. Distributed Batched Grading Matrix

```
   Total Submitted Attempts (e.g., 500)
              │
   ┌──────────┴──────────┐──────────┐
   ▼          ▼          ▼          ▼
Batch A     Batch B    Batch C    Batch D
#001–#125  #126–#250  #251–#375  #376–#500
Grader 1   Grader 2   Grader 3   Grader 4
48hr SLA   48hr SLA   48hr SLA   48hr SLA
   │          │          │          │
   ▼          ▼          ▼          ▼
 Auto-grade MCQs (instant) + Manual Short/Long
   │
   ▼
  DRAFT → MARKED (Locked)
          │
          ▼
 Designer / Chief Examiner Moderation (GradeModeration)
          │
          ▼
    Result Publication (Explicit Release by Designer)
          │
          ▼
    Participant Results Portal Unlocked
```

### Grading Rules:
1. Partitions by numerical index ranges **or** by section specializations (e.g., Grader 1 scores Section B Physics).
2. Double-Blind: Candidate shown as `CAND-78492`, name masked.
3. MCQ auto-scored, Grader verifies edge cases.
4. Draft (partial) and Marked (final) states with audit trail.
5. Designer can modify batch assignments before marking begins.
6. Chief Examiner moderation step available before result publication.

---

## 9. Result Publication & Visibility Control

* **Before Release:** Participants see `"Results: Pending Evaluation"` on their exam history.
* **Release Action:** Designer explicitly clicks **"Publish Results"** per exam. Triggers:
  1. Sets `Exam.results_published = True`.
  2. Creates a `Notification` of type `RESULT_PUBLISHED` for all enrolled participants.
  3. Participants can now access full scorecard, section breakdown, and grader feedback (if designer enabled `show_grader_feedback`).
* **Grader Access Post-Publication:** Graders can still view their evaluations but must request a Designer unlock to modify.

---

## 10. Non-Functional Requirements (NFR)

### 10.1 Performance & Scalability
| Metric | Target |
|---|---|
| Lobby & Cockpit TTFB | < 150ms |
| Heartbeat API response | < 50ms under 2,000 concurrent candidates |
| Database engine | SQLite (dev/offline) / PostgreSQL 16+ (production) |
| Concurrent candidates | Tier-dependent (100 Starter / 500 Professional / Unlimited Enterprise) |

### 10.2 Security & Integrity
| Control | Mechanism |
|---|---|
| CSRF Protection | Django `CsrfViewMiddleware` on all state-changing requests |
| XSS Protection | Template auto-escaping + strict Content Security Policy |
| Server Clock | Server-authoritative timer; client clock only for UX display |
| Role Isolation | Custom RBAC mixins; no role elevation without Super Admin grant |
| Tenant Isolation | Middleware-enforced `request.tenant`; queryset-level tenant scoping |

### 10.3 Accessibility & Design Standards
* WCAG 2.1 AA color contrast compliance on all UI components.
* Screen-reader-friendly: All icons have `aria-label`, form fields have explicit `<label>` elements.
* Fully responsive layouts (supports 1024px, 1366px, 1920px desktop widths; exam cockpit is desktop-only by design for security).
* Comprehensive on-page guide text and colorful icons on all configuration pages explaining each setting.

---

## 11. Scenarios & End-to-End Walkthroughs

### Scenario A: Power Outage & Browser Crash Recovery
1. Student *Zaid* is at Question 24 of 50, 32 minutes remaining, has answered 23 questions.
2. Power blackout — computer shuts down immediately.
3. Power restored 3 minutes later. Zaid navigates to the exam URL on any terminal.
4. `TenantResolutionMiddleware` identifies tenant. `ExamAttempt` status shows `IN_PROGRESS`.
5. Server recalculates `remaining_seconds = deadline - now()`. Loads all 23 saved `AttemptAnswer` records.
6. Cockpit re-launches at Question 24. Zero data lost. Timer resumes from server-calculated value.

### Scenario B: Dynamic Time Extension During Live Exam
1. Designer broadcasts: *"Question 14 has been clarified — a correction note has been issued."*
2. Designer clicks `+10 Minutes` → `ALL`.
3. Service: `grant_bonus_time_to_exam(exam, bonus_minutes=10, ...)` runs atomically.
4. All 300 active heartbeat responses return `remaining_seconds` increased by 600.
5. Each cockpit timer smoothly increments. A toast appears: *"Supervisor added 10 minutes."*
6. `ExamLiveEvent` record created, `AuditLog` entry written.

### Scenario C: Full Exam Lifecycle (Happy Path)
1. **Designer** creates `Exam: CS-401-2026`, sets duration 90 min, opens at 09:00, enables fullscreen + 3-tab limit.
2. **Item Writer** adds 50 MCQs and 2 Long Essays to the question bank.
3. **Designer** assigns questions to sections, sets weightages, enables 50:50 and Skip lifelines (max 2 each).
4. **Designer** imports participant roster (300 students via CSV). Assigns 3 Graders (100 each).
5. **Participants** log in at 09:00, enter lobby, read instructions, click "Start Exam".
6. Exam runs 90 minutes with live monitoring in the Control Room.
7. After all submissions: MCQs auto-scored. Graders evaluate Short/Long questions.
8. **Designer** monitors SLA progress. Sends reminder to Grader 2 at 40% completion.
9. All graders finalize (`MARKED`). Designer reviews moderation, clicks **"Publish Results"**.
10. **Participants** receive `RESULT_PUBLISHED` notification. View scorecards and feedback.

### Scenario D: Item Writer Collaboration
1. Designer creates Exam draft and authorizes Item Writer "Prof. Ahmed" to add questions to `CS-401-2026`.
2. Prof. Ahmed logs into his dashboard, sees only the authorized exams.
3. He adds 20 MCQs including 3 image-based diagrams (locally stored, offline accessible).
4. Designer reviews added questions in the Quality Review Queue and approves.
