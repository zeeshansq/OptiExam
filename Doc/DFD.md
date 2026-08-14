# Data Flow Diagrams (DFD) — OptiExam System
**Document Version:** 1.0.0  
**Project:** OptiExam Assessment Platform  
**Target Format:** Structured Markdown with Visual Mermaid Diagrams & Data Dictionaries  

---

## 1. DFD Level 0: Context Diagram

The Level 0 Context Diagram establishes the boundary of the OptiExam system and its interactions with the **5 External Entities**.

```mermaid
graph TD
    %% External Entities
    SA[Super Admin]
    DES[Designer / Tenant Admin]
    IW[Item Writer]
    GRD[Grader]
    PAR[Participant / Candidate]

    %% Main System Process
    SYS((0.0<br/>OptiExam<br/>Assessment Engine))

    %% Super Admin Flows
    SA -->|1. Tenant Creation & Tier Config| SYS
    SYS -->|2. Global Metrics & Audit Logs| SA

    %% Designer Flows
    DES -->|3. Exam Config, Rules, Weightages| SYS
    DES -->|4. Grader Batch Allocations| SYS
    DES -->|5. Live Ops: Add Time / Force Start / Broadcast| SYS
    SYS -->|6. Real-time Exam & Grading Progress| DES

    %% Item Writer Flows
    IW -->|7. Questions, Options, Images, Rubrics| SYS
    SYS -->|8. Question Review & Usage Stats| IW

    %% Grader Flows
    GRD -->|9. Evaluation Scores, Feedback, Draft/Final| SYS
    SYS -->|10. Assigned Batches & Model Answers| GRD

    %% Participant Flows
    PAR -->|11. Auth, Attempt Answers, Lifelines, Heartbeats| SYS
    SYS -->|12. Exam Questions, Timer, Results, Feedback| PAR
```

---

## 2. DFD Level 1: Subsystem Decomposition

The Level 1 Diagram decomposes OptiExam into 6 core subsystems and 8 persistent data stores.

```mermaid
graph TD
    %% External Entities
    SA[Super Admin]
    DES[Designer]
    IW[Item Writer]
    GRD[Grader]
    PAR[Participant]

    %% Subsystems / Processes
    P1((1.0<br/>Tenant & User<br/>Management))
    P2((2.0<br/>Question Bank<br/>Authoring Engine))
    P3((3.0<br/>Exam Blueprint &<br/>Config Engine))
    P4((4.0<br/>Live Exam Engine &<br/>Proctoring Cockpit))
    P5((5.0<br/>Batched Grading &<br/>Evaluation Engine))
    P6((6.0<br/>Notification &<br/>Broadcast Engine))

    %% Data Stores
    DS1[(DS-1: Tenants & Features)]
    DS2[(DS-2: Accounts & Profiles)]
    DS3[(DS-3: Question Banks & Rubrics)]
    DS4[(DS-4: Exam Blueprints & Lifelines)]
    DS5[(DS-5: Exam Attempts & Answers)]
    DS6[(DS-6: Proctoring Logs & Heartbeats)]
    DS7[(DS-7: Grader Allocations & Scores)]
    DS8[(DS-8: Notifications & Broadcasts)]

    %% Connections for P1: Tenant & User Mgmt
    SA -->|Tenant Specs| P1
    DES -->|User Rosters| P1
    P1 <-->|Read/Write Tenant Data| DS1
    P1 <-->|Read/Write Credentials & Roles| DS2

    %% Connections for P2: Question Authoring
    IW -->|Questions, Options, Rubrics, Images| P2
    P2 <-->|CRUD Questions & Media| DS3

    %% Connections for P3: Exam Blueprint & Config
    DES -->|Exam Rules, Schedule, Sections, Lifelines| P3
    P3 -->|Attach Questions| DS3
    P3 <-->|Read/Write Exam Config| DS4

    %% Connections for P4: Live Exam Engine
    PAR -->|Start Request, Answers, Heartbeat| P4
    P4 <-->|Verify Exam & Lifelines| DS4
    P4 <-->|Save/Resume Attempt State| DS5
    P4 -->|Log Security Events| DS6
    P4 -->|Deliver Active Question Stream| PAR

    %% Connections for P5: Batched Grading
    DES -->|Batch Allocations 1-100, 101-200| P5
    GRD -->|Scores, Notes, Rubric Levels| P5
    P5 <-->|Read Submissions| DS5
    P5 <-->|Read Rubrics & Model Answers| DS3
    P5 <-->|Store Allocations & Question Scores| DS7
    P5 -->|Update Final Exam Score| DS5

    %% Connections for P6: Notification & Broadcasts
    DES -->|Live Broadcast / +Time Notice| P6
    P6 -->|Write Notification| DS8
    P6 -->|Real-time Toast Alert| PAR
    P6 -->|Grading SLA Alert| GRD
```

---

## 3. DFD Level 2: Detailed Process Workflows

### 3.1 Process 4.0: Live Examination & Anti-Cheating Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student as Participant (Browser)
    participant UI as Exam Cockpit (Offline-Ready JS)
    participant API as OptiExam Server Engine
    participant DB_A as DS-5: Exam Attempts & Answers
    participant DB_P as DS-6: Proctoring Logs
    participant DB_E as DS-4: Exam Config & Live Events

    Student->>UI: Clicks "Start Exam"
    UI->>API: POST /api/v1/exams/{id}/start/ (Session Nonce)
    API->>DB_E: Fetch Exam Schedule & Anti-Cheating Rules
    API->>DB_A: Create/Load ExamAttempt (Calculate Remaining Time)
    API-->>UI: Return Seeded Questions, Allowed Lifelines, Server Clock
    UI->>UI: Enter Fullscreen Mode & Attach Anti-Cheating Event Shields

    loop Every 15 Seconds (Heartbeat Cycle)
        UI->>API: POST /api/v1/attempts/{id}/heartbeat/ (Active Question, Answers Delta)
        API->>DB_A: Upsert AttemptAnswers (Auto-save)
        API->>DB_E: Check Active Broadcasts / Extra Time Grants (+10 Mins)
        API-->>UI: Acknowledge Sync + Return Updated Time / Broadcast Messages
    end

    alt Tab Switch / Fullscreen Exit Detected
        UI->>API: POST /api/v1/attempts/{id}/violation/ (Event: TAB_BLUR, Count: N)
        API->>DB_P: Log Proctoring Violation
        API-->>UI: Return Warning Modal (e.g. Warning 1 of 3)
    end

    alt Candidate Applies "50:50 Lifeline"
        UI->>API: POST /api/v1/attempts/{id}/lifeline/ (Type: FIFTY_FIFTY, Question: Q12)
        API->>DB_A: Decrement Lifeline Quota & Return 2 Struck-Out Options
        API-->>UI: Disable 2 Incorrect Options in DOM
    end

    Student->>UI: Clicks "Submit Examination"
    UI->>API: POST /api/v1/attempts/{id}/submit/
    API->>DB_A: Mark Attempt State as SUBMITTED & Lock Inputs
    API->>DB_A: Trigger Automated MCQ Auto-Scoring Engine
    API-->>UI: Render Submission Receipt & Completion Dashboard
```

---

### 3.2 Process 5.0: Distributed Batched Grading & Evaluation Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Designer as Designer (Admin)
    actor Grader as Grader (Evaluator)
    participant Engine as Grading Allocation Service
    participant DB_G as DS-7: Grader Allocations & Scores
    participant DB_A as DS-5: Attempt & Answers
    participant DB_R as DS-3: Question Rubrics

    Designer->>Engine: Configure Batching: Attempt #001–#100 -> Grader 1, #101–#200 -> Grader 2
    Engine->>DB_G: Create GraderAllocation records (Target Batches + SLA Deadlines)
    
    Grader->>Engine: Open Grader Dashboard
    Engine->>DB_G: Retrieve Assigned Batches for Current Grader
    Engine-->>Grader: Display Assigned Submissions Queue

    Grader->>Engine: Select Candidate Attempt (Double-Blind Anonymized)
    Engine->>DB_A: Fetch Student Submissions (Short/Long Answers)
    Engine->>DB_R: Fetch Model Answers & Criteria Rubrics
    Engine-->>Grader: Render Split-Screen Grading Cockpit

    Grader->>Engine: Enter Scores, Select Rubric Criteria, Add Feedback (State: DRAFT)
    Engine->>DB_G: Save Partial Evaluation (QuestionScore.is_draft = True)

    Grader->>Engine: Submit Finalized Evaluation (State: MARKED)
    Engine->>DB_G: Finalize Scores (QuestionScore.is_draft = False)
    Engine->>DB_A: Recompute Total Exam Score & Mark Attempt GRADED
    Engine-->>Designer: Update Live Grading SLA Progress Bar (e.g., Grader 1: 100%)
```

### 3.3 Process 7.0: Bulk Data Ingestion, Dry-Run Validation & Commit Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Designer / Item Writer
    participant UI as Import Hub UI (Web)
    participant Svc as Import Engine Service
    participant Val as Dry-Run Validator
    participant DB as Target Data Store (DS-2/DS-3/DS-4/DS-9)

    User->>UI: Clicks "Download Sample Template (.CSV / .XLSX)"
    UI-->>User: Delivers Pre-Formatted Sample File with Instructions

    User->>UI: Uploads Data File (CSV / XLSX / ZIP)
    UI->>Svc: POST /api/v1/imports/validate/ (File Payload)
    Svc->>Val: Parse Headers & Validate Row Schemas (Types, Enums, Foreign Keys)
    
    alt Validation Errors Found
        Val-->>Svc: Error Matrix (Row Numbers, Field Names, Reasons)
        Svc-->>UI: Return 422 with Detailed Error Audit Table
        UI-->>User: Highlight Erroneous Rows with Remediation Guide
    else Validation Succeeded
        Val-->>Svc: Parsed Clean Records (Count: N)
        Svc->>DB: Save DataImportJob (Status: PREVIEW_READY, Preview: First 10 Rows)
        Svc-->>UI: Return 200 OK + 10-Row Confirmation Preview Grid
        UI-->>User: Render Preview Grid + Prompt "Commit Import"
    end

    User->>UI: Clicks "Commit Import"
    UI->>Svc: POST /api/v1/imports/commit/ (Job ID)
    Svc->>DB: Atomic Bulk Ingestion (User/Question/Roster records created)
    Svc->>DB: Update DataImportJob (Status: COMPLETED, Successful: N)
    Svc-->>UI: Return Success Summary Receipt
    UI-->>User: Display Ingestion Confirmation & Deep Links
```

---

## 4. Comprehensive Data Store & Flow Dictionary

| Data Flow ID | Flow Name | Source | Destination | Data Attributes / Payload Fields |
|---|---|---|---|---|
| **DF-01** | Tenant Registration | Super Admin | DS-1 | `name`, `slug`, `domain`, `tier`, `max_concurrent_users`, `feature_flags` |
| **DF-02** | Exam Blueprint Config | Designer | DS-4 | `title`, `code`, `start_time`, `end_time`, `duration_mins`, `pass_mark`, `lifeline_rules`, `anti_cheat_rules` |
| **DF-03** | Question Creation | Item Writer | DS-3 | `type` (MCQ, Image, Short, Long), `prompt_text`, `options_json`, `image_asset`, `model_answer`, `rubric_schema` |
| **DF-04** | Heartbeat & Auto-Save | Participant UI | DS-5 | `attempt_id`, `question_id`, `selected_options`, `text_answer`, `time_remaining_client`, `client_timestamp` |
| **DF-05** | Proctoring Incident | Participant UI | DS-6 | `attempt_id`, `violation_type` (`BLUR`, `FULLSCREEN_EXIT`, `KEY_LOCK`), `snapshot_ts`, `incident_count` |
| **DF-06** | Live Time Extension | Designer | DS-4 / DS-8 | `exam_id`, `target_type` (`ALL` or `SINGLE_USER`), `extra_minutes`, `reason`, `issued_at` |
| **DF-07** | Grader Allocation | Designer | DS-7 | `exam_id`, `grader_id`, `candidate_range_start`, `candidate_range_end`, `sla_deadline` |
| **DF-08** | Question Evaluation | Grader | DS-7 | `attempt_id`, `question_id`, `awarded_marks`, `rubric_criteria_selected`, `grader_notes`, `is_draft` |
| **DF-09** | System Notification | Notification Svc | DS-8 | `tenant_id`, `recipient_id`, `title`, `body`, `action_url`, `is_read`, `priority` |
| **DF-10** | Bulk Data Import | Designer / Item Writer | DS-9 / DS-2/3/4 | `import_type`, `source_file`, `status`, `total_rows`, `preview_data`, `error_log`, `target_id` |

---

## 5. Failure & Edge Case Data Flows

### 5.1 Network Dropout During Sync
* If client fails to reach server on heartbeat:
  1. Offline JS Engine writes payload to browser `localStorage` under `optiexam_offline_queue`.
  2. Cockpit displays non-blocking amber badge: *"Offline Mode: Answers safely stored locally"*.
  3. Exponential backoff retry occurs at 3s, 6s, 12s.
  4. On connection recovery, queued answers are flushed in a single bulk sync transaction.

### 5.2 Concurrent Examiner Score Updates
* `QuestionScore` records utilize optimistic concurrency locking with `version` fields to prevent two graders from overwriting the same candidate's essay score simultaneously.

### 5.3 Malformed or Corrupt Bulk Import Files
* If uploaded CSV/Excel contains malformed rows, missing mandatory headers, or invalid foreign keys:
  1. Dry-run parser rejects ingestion before any database writes occur.
  2. Generates line-by-line `error_log` JSON with column names and error messages.
  3. UI renders an interactive error table with 1-click "Download Error Report" so the user can fix erroneous cells in Excel and re-upload.

