<div align="center">

<br/>

<h1>&#9889; OptiExam</h1>

<p><strong>Next-Generation Multi-Institutional High-Stakes Examination &amp; Assessment Platform</strong></p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-003B57?style=for-the-badge&logo=postgresql&logoColor=white" alt="DB" />
  <img src="https://img.shields.io/badge/Tests-33%20Passing-10B981?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/CDN-Zero%20Dependencies-F59E0B?style=for-the-badge" alt="Offline" />
  <img src="https://img.shields.io/badge/License-Commercial-EF4444?style=for-the-badge" alt="License" />
</p>

<p>
  <a href="#-why-optiexam">Why OptiExam</a> &bull;
  <a href="#-feature-highlights">Features</a> &bull;
  <a href="#-system-architecture">Architecture</a> &bull;
  <a href="#-setup--installation-guide">Setup</a> &bull;
  <a href="#-data-flow-diagrams">Data Flow</a> &bull;
  <a href="#-case-studies--real-world-scenarios">Case Studies</a> &bull;
  <a href="#-author--contact">Contact</a>
</p>

<br/>

> **"From question authoring to published scorecards — OptiExam orchestrates the entire examination lifecycle in a single, sovereign, offline-capable platform."**

<br/>

</div>

---

## Table of Contents

- [Why OptiExam?](#-why-optiexam)
- [Who Is It For?](#-who-is-it-for)
- [Feature Highlights](#-feature-highlights)
- [System Architecture](#-system-architecture)
- [Data Flow Diagrams](#-data-flow-diagrams)
- [5-Tier Role System](#-5-tier-role-system)
- [Tech Stack](#-tech-stack)
- [Setup and Installation Guide](#-setup--installation-guide)
- [Database Seeding (Pakistani Demo Data)](#-database-seeding-pakistani-demo-data)
- [Project Structure](#-project-structure)
- [Case Studies and Real-World Scenarios](#-case-studies--real-world-scenarios)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Author and Contact](#-author--contact)

---

## Why OptiExam?

Most examination systems are either too simple (basic quiz tools) or too rigid (expensive enterprise LMS modules). **OptiExam fills the critical gap** — purpose-built for institutions that demand rigour at every step of the assessment lifecycle.

```
+-------------------------------------------------------------------+
|                                                                   |
|  AUTHORING  -->  CONFIGURATION  -->  LIVE PROCTORING  -->  GRADING|
|       -->  MODERATION  -->  PUBLICATION  -->  ANALYTICS           |
|                                                                   |
|  One platform. Zero third-party dependencies.                     |
|  Deployable on-premise. Offline-ready. Multi-institution.         |
|                                                                   |
+-------------------------------------------------------------------+
```

### What Makes OptiExam Different?

| Challenge | Typical Solutions | OptiExam Approach |
|-----------|-------------------|-------------------|
| **Exam Integrity** | Basic browser lock | Multi-vector anti-cheat: fullscreen enforcement, clipboard lock, DevTools block, tab-switch detection, 15-second heartbeat |
| **Internet Dependency** | Cloud-only CDN assets | **100% offline-ready** — all fonts, icons, scripts bundled locally; works in air-gapped environments |
| **Scale and Isolation** | Single-institution systems | **True multi-tenancy** — isolated workspaces, branding, question banks per institution with zero data leakage |
| **Grading Fairness** | Manual assignment | **Double-blind batched grading** — candidate names anonymized as `CAND-XXXXX`, SLA deadlines, Chief Examiner moderation |
| **Resilience** | Exam crashes = data loss | **Crash recovery engine** — localStorage offline queue auto-resumes exact question state after power outage |
| **Analytics Depth** | Basic pass/fail counts | Psychometric item analysis: p-values, discrimination index (D-index), Bloom's Taxonomy heatmaps |

---

## Who Is It For?

| Educational Institutions | Corporate and Certification Bodies |
|--------------------------|------------------------------------|
| Universities (midterms, finals, entrance exams) | HR assessment centers |
| Medical / Engineering Colleges (objective + subjective boards) | Professional certification authorities |
| Schools (standardized term assessments) | Government examination boards |
| Professional Training Academies | Corporate learning and development wings |

---

## Feature Highlights

### Ironclad Anti-Cheat Proctoring Engine

```
Browser opens fullscreen --> DOM event shields attach
   --> Clipboard (copy/paste) blocked
   --> DevTools keyboard shortcuts intercepted
   --> Tab-switch/window blur events logged
   --> 15-second heartbeat syncs answers to server
   --> Violation count increments --> warn --> auto-submit
```

- Configurable violation threshold per exam (e.g., max 3 tab switches before auto-submit)
- All proctoring events stored with timestamps in `ProctoringLog`
- Real-time Designer alert: candidate violation events appear on Live Ops matrix instantly

---

### 5 Question Formats — All in One Authoring Studio

| # | Format | Use Case | Grading |
|---|--------|----------|---------|
| 1 | **Single-Choice MCQ** | Objective recall and comprehension | Automated with negative marking |
| 2 | **Multiple-Choice MCQ** | Multi-concept evaluation | Automated with configurable partial marks |
| 3 | **Picture / Diagram MCQ** | Visual anatomy, circuit analysis, tree rotations | Automated with local image upload |
| 4 | **Short Answer** | Conceptual explanation, definitions | Manual with word-limit enforcement |
| 5 | **Long Essay / Structured** | System design, clinical pathophysiology, case analysis | Manual rubric-based per-criteria scoring |

Each question supports: Bloom's Taxonomy level, difficulty tier, topic tags, hint text (for the Hint lifeline), and post-exam per-option explanations.

---

### Lifeline Engine — Gamified Academic Fairness

Configure per exam which lifelines candidates may use and how many times:

| Lifeline | Effect | Config |
|----------|--------|--------|
| **50:50 Eliminator** | Removes 2 wrong MCQ options using server-side seeded logic | Max uses: 1-5 |
| **Skip Question** | Temporarily skip and revisit — question flagged in palette | Max uses: 1-10 |
| **Hint Token** | Reveals authored hint text for the question | Max uses: 1-5 |
| **Bookmark Flag** | Tags question for later review — visual indicator on palette | Max uses: unlimited |

---

### Designer Live Ops Command Center

Real-time exam oversight — no page refresh required:

```
+------------------------------------------------------------------+
|   CS401 LIVE OPS: 87 candidates active  |  00:42:15 remaining   |
+------------------------------------------------------------------+
|  CAND-001 [ACTIVE]  Q7/12    CAND-002 [ACTIVE]  Q3/12           |
|  CAND-003 [WARN ]   Q9/12    CAND-004 [LOBBY ]  --              |
+------------------------------------------------------------------+
|  [+5 Mins All]  [+10 Mins]  [Force Start]  [Broadcast Alert]   |
+------------------------------------------------------------------+
```

- **Bonus time injection**: grant +5/+10/+15/custom minutes to all or individual candidates
- **Force-start**: manually enable exam for a candidate outside schedule window
- **Live broadcasts**: send real-time toast alerts visible inside every candidate's exam cockpit
- **Force-submit**: close an individual candidate's attempt when needed

---

### Distributed Batched Grading Matrix

```
Exam CS302 Submitted (200 candidates, 4 graders)
         |
Designer creates batch allocation:
   --> Grader Zainab: Candidates #001-#050  (SLA: 12 hours)
   --> Grader Tariq:  Candidates #051-#100  (SLA: 18 hours)
         |
Each grader enters split-screen cockpit:
   LEFT:  Student submission (anonymized: CAND-XXXXX)
   RIGHT: Model answer + Rubric criteria (per-criterion marks)
         |
Draft --> Save --> Finalize --> Chief Examiner Moderation
         |
Designer publishes results --> Candidates see scorecards
```

---

### Psychometric Analytics Hub

After results publication, the head of examinations accesses:

- **Score Distribution Histogram** — canvas-rendered, no external chart libraries
- **Pass/Fail Ratio Ring Chart** — cohort performance at a glance
- **Item Analysis Scatter Plot** — difficulty (p-value) vs. discrimination (D-index) per question
- **Bloom's Taxonomy Breakdown** — per-level average score across the cohort
- **Section-wise Performance Comparison** — identify weak curriculum areas

---

## System Architecture

### Module Map

```
OptiExam/
|
+-- apps/
|   +-- core/          <- Tenant middleware, RBAC mixins, audit, health check
|   +-- tenants/       <- Multi-institution management, feature flags, branding
|   +-- accounts/      <- Custom 5-tier User model, login, profile, notifications
|   +-- exams/         <- Blueprint builder, sections, scheduling, lifelines, Live Ops
|   +-- questions/     <- Question banks, 5 formats, rubrics, bulk CSV import
|   +-- submissions/   <- Candidate cockpit, heartbeat, anti-cheat, crash recovery
|   +-- grading/       <- Batch allocations, split-screen studio, moderation
|   +-- notifications/ <- In-app alerts, SLA reminders, exam broadcasts
|
+-- optiexam/settings/
|   +-- base.py        <- Shared config (INSTALLED_APPS, MIDDLEWARE, AUTH)
|   +-- local.py       <- Dev: SQLite, DEBUG=True
|   +-- production.py  <- Prod: PostgreSQL, WhiteNoise, SECURE flags
|
+-- static/
|   +-- fonts/         <- Inter, Outfit, JetBrains Mono (WOFF2, zero CDN)
|   +-- icons/         <- lucide-sprite.svg (offline Lucide icon set)
|   +-- css/           <- optiexam-core.css, optiexam-theme.css, cockpit.css
|   +-- js/            <- optiexam-core.js, anti-cheat-shield.js, heartbeat-sync.js
|
+-- templates/
    +-- base.html
    +-- accounts/      <- Login (70/30 split layout), profile
    +-- exams/         <- Blueprint editor, live ops, analytics
    +-- submissions/   <- Lobby, cockpit, results, history
    +-- grading/       <- Batch queue, evaluation studio, moderation
```

### Service Layer Pattern (Clean Architecture)

```
HTTP Request
    |
    v
View (Class-Based) --- Authentication, permission check, HTTP handling only
    |
    v
Service Layer -------- @transaction.atomic business logic, state transitions
    |
    v
Selector Layer ------- Optimized read queries, aggregations, prefetch
    |
    v
Model Layer ---------- Field constraints, simple properties, __str__
    |
    v
Database (SQLite / PostgreSQL)
```

---

## Data Flow Diagrams

### Level 0 — Context Diagram

```
                +---------------------------------------+
                |       OptiExam Assessment Engine      |
                |                                       |
  Super Admin -> |  Institution Onboarding and Quotas   |
  Designer    -> |  Exam Design and Grader Allocation   |
  Item Writer -> |  Question Authoring and Rubrics      | -> Item Writer
  Grader      -> |  Evaluation and Scoring              | -> Grader
  Candidate   -> |  Login -> Attempt -> Results         | -> Candidate
                +---------------------------------------+
```

### Level 1 — Exam Lifecycle Subsystems

```mermaid
graph LR
    A["Item Writer"] -->|Authoring| B["Question Bank Engine"]
    B --> C["Exam Blueprint Config"]
    D["Designer"] -->|Blueprint and Roster| C
    C --> E["Live Exam Engine and Cockpit"]
    F["Candidate"] -->|Attempt + Heartbeats| E
    E --> G["Anti-Cheat and Proctoring Log"]
    E --> H["Batched Grading Matrix"]
    D -->|Batch Allocations| H
    I["Grader"] -->|Scores and Rubrics| H
    H --> J["Grade Moderation Engine"]
    D -->|Approve / Adjust| J
    J --> K["Results Publication and Scorecards"]
    K --> L["Psychometric Analytics Hub"]
    F -->|View Scorecard| K
```

### Level 2 — Live Exam Data Flow (Sequence)

```
Candidate Browser              OptiExam Server              Database
      |                               |                          |
      |-- Click "Start Exam" -------> |                          |
      |                               |-- Verify schedule -----> |
      |                               | <-- Seeded questions --- |
      | <-- Questions + Timer ------- |                          |
      |                               |                          |
      |  [ Every 15 Seconds ]         |                          |
      |-- Heartbeat + Answer Delta -> |                          |
      |                               |-- Upsert answers ------> |
      |                               | <-- Live events / +Time- |
      | <-- Ack + Updated Timer ----- |                          |
      |                               |                          |
      |  [ Tab Switch Detected ]      |                          |
      |-- Violation Event ----------> |                          |
      |                               |-- Log ProctoringLog ---> |
      | <-- Warning Modal (1 of 3) -- |                          |
      |                               |                          |
      |-- Submit / Auto-submit -----> |                          |
      |                               |-- Finalize Attempt ----> |
      | <-- Submission Receipt ------- |                         |
```

### Level 2 — Grading Pipeline

```
Designer creates batch allocation
      |
      +--> Grader A: Candidates 001-100 (SLA: 24h)
      +--> Grader B: Candidates 101-200 (SLA: 24h)
               |
               | [ Double-Blind Split-Screen Cockpit ]
               | LEFT:  CAND-XXXXX submission (anonymized)
               | RIGHT: Model Answer + Rubric Matrix
               |
               +--> Save as DRAFT (partial scoring)
               +--> FINALIZE (locked unless reopened)
                         |
                    Chief Examiner Review
                         |
                    +--> APPROVED  (publish as-is)
                    +--> ADJUSTED  (modify score + note)
                    +--> RETURNED  (send back to grader)
                              |
                         Results Published
                              |
                    +------------------------+
                    |   Candidate Scorecard  |
                    |  - Section breakdown   |
                    |  - Grader feedback     |
                    |  - Rubric per answer   |
                    |  - Print PDF button    |
                    +------------------------+
```

---

## 5-Tier Role System

```
           +-------------------------------------------+
           |       SUPER ADMIN (SaaS Platform)         |
           |  Provision institutions, quotas, flags     |
           +---------------------+---------------------+
                                 |
           +---------------------v---------------------+
           |      DESIGNER (Institution Head)          |
           |  Exam design, grader allocation, Live Ops |
           +----------+--------------------+-----------+
                      |                    |
    +-----------------v-------+  +---------v------------------+
    |       ITEM WRITER        |  |           GRADER           |
    |  Questions, Rubrics, Tags|  |  Scoring, Feedback, SLA    |
    +-------------------------+  +----------------------------+
                      |
           +----------v---------------------------------+
           |         PARTICIPANT / CANDIDATE           |
           |  Lobby -> Cockpit -> History -> Scorecard |
           +-------------------------------------------+
```

| Role | Dashboard URL | Key Permissions |
|------|---------------|-----------------|
| **Super Admin** | `/admin/saas/dashboard/` | Institution CRUD, Feature Flags, Global Audit Logs |
| **Designer** | `/dashboard/` | Exam blueprint, Live Ops, Grader allocation, Analytics |
| **Item Writer** | `/questions/` | Question bank CRUD, 5 formats, bulk import |
| **Grader** | `/grading/` | Assigned batch queue, split-screen evaluation, rubric scoring |
| **Candidate** | `/lobby/` | Exam lobby, live cockpit, history, results |

---

## Tech Stack

| Layer | Technology | Details |
|-------|------------|---------|
| **Backend** | Django 5.x / Python 3.12+ | Class-based views, service/selector pattern |
| **ORM and Database** | SQLite (dev) / PostgreSQL (prod) | Dual-engine, zero reconfiguration |
| **Auth and Security** | Custom User model + Session auth | 5-tier RBAC, audit logging |
| **Configuration** | django-environ | .env file based config |
| **Image Handling** | Pillow | Local image uploads for Diagram MCQs |
| **Data Import** | openpyxl | CSV/XLSX roster and question bulk import |
| **Frontend** | Vanilla HTML5 + Vanilla CSS + ES6+ | Zero framework dependency |
| **Typography** | Inter, Outfit, JetBrains Mono | WOFF2 bundled locally (zero CDN) |
| **Icons** | Lucide SVG Sprite | Local bundle, offline-ready |
| **Design** | CSS Custom Properties + Glassmorphism | Dark/Light theme, design tokens |
| **Charts** | Native HTML5 Canvas | No Chart.js or D3.js CDN required |
| **Exam Engine JS** | anti-cheat-shield.js + heartbeat-sync.js | Custom-built, no library dependencies |
| **Testing** | pytest + pytest-django | 33 tests, CI-ready |

> **Zero External CDN Policy** — No runtime requests to `fonts.googleapis.com`, `cdnjs.cloudflare.com`, `unpkg.com`, or any external host. Fully air-gap deployable.

---

## Setup and Installation Guide

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12+ | [python.org/downloads](https://www.python.org/downloads/) |
| pip | Latest | Included with Python |
| Git | Any | For cloning the repository |
| PostgreSQL | 14+ (optional) | SQLite is used by default for development |

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/zeeshansq/OptiExam.git
cd OptiExam
```

---

### Step 2 — Create and Activate Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt

# Development and testing tools
pip install -r requirements-dev.txt
```

---

### Step 4 — Configure Environment Variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and configure:

```env
# Core Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (SQLite for dev — no extra setup needed)
DATABASE_URL=sqlite:///db.sqlite3

# For production PostgreSQL:
# DATABASE_URL=postgres://user:password@localhost:5432/optiexam_db

# Show Quick Demo Login palette on the login page
ENABLE_DEMO_LOGINS=True

LOG_LEVEL=INFO
```

---

### Step 5 — Initialize Database and Seed Demo Data

```bash
# Recommended: Seed with Pakistani demo data (auto-runs migrations)
python manage.py seed_pakistan_data

# Clear existing data and re-seed fresh
python manage.py seed_pakistan_data --clear

# Migrations only (no demo data)
python manage.py migrate
```

> The seeder automatically runs all pending migrations, provisions 4 Pakistani institutions (NUST, FAST-NUCES, KEMU, NED), creates 21 user accounts across all 5 roles, authors 24 questions across 4 question banks (all 5 formats), creates 5 exam blueprints with 18 sections and 40 assignments, and generates `DEMO_CREDENTIALS.txt` at the project root.

---

### Step 6 — Run the Development Server

```bash
python manage.py runserver
```

Open: **http://127.0.0.1:8000/auth/login/**

---

### Step 7 — Quick Login (Demo Mode)

Use the Quick Role Access palette on the login page, or reference `DEMO_CREDENTIALS.txt`:

| Role | Username | Password |
|------|----------|----------|
| Super Admin | `admin` | `OptiExam@2026!` |
| Designer | `dr.sarah.khan` | `OptiExam@2026!` |
| Item Writer | `prof.ahmed.bilal` | `OptiExam@2026!` |
| Grader | `grader.zainab` | `OptiExam@2026!` |
| Candidate (Exam Ready) | `ali.hassan` | `OptiExam@2026!` |

> **Single-click** any role icon on the login page to auto-fill credentials.  
> **Double-click** to fill and immediately submit without confirmation prompts.

---

### Production Deployment Checklist

```bash
# 1. Production environment variables
DEBUG=False
DATABASE_URL=postgres://user:pass@host:5432/optiexam
SECRET_KEY=<cryptographically-random-50-char-key>
ALLOWED_HOSTS=yourdomain.com

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Apply migrations
python manage.py migrate

# 4. Create super admin
python manage.py createsuperuser

# 5. Serve with Gunicorn
gunicorn optiexam.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Database Seeding (Pakistani Demo Data)

```bash
python manage.py seed_pakistan_data          # Fresh seed (auto-migrates)
python manage.py seed_pakistan_data --clear  # Wipe all data and re-seed
```

### Seeded Data Summary

```
==============================================================================
  PAKISTANI DOMAIN SEEDING COMPLETED SUCCESSFULLY
==============================================================================
  Institutions Provisioned  :  4  (NUST, FAST-NUCES, KEMU, NED)
  User Accounts Created     :  21 (all 5 roles, Pakistani personas)
  Question Banks            :  4
  Questions Authored        :  24 (all 5 formats represented)
  Exam Blueprints           :  5
  Sections Created          :  18 across all blueprints
  Question Assignments      :  40 assigned across sections
  Roster Enrollments        :  35
  Completed Attempts        :  17 (with scores, grading, moderation)
  Live In-Progress Sessions :  2  (visible in Live Ops Command Center)
  Unattempted Live Exam     :  CS101 -- 4 sections, 10 questions, ZERO attempts
                               Login as ali.hassan and take the live exam now!
==============================================================================
```

### 4 Ready-to-Test Scenarios

| Scenario | Exam Code | State | What to Test |
|----------|-----------|-------|--------------|
| **A — Published Results** | `MID-2026-CS401` | Results released | Scorecard, section breakdown, analytics, item analysis |
| **B — Grading Queue** | `MID-2026-CS302` | Pending evaluation | Grader dashboard, split-screen cockpit, rubric moderation |
| **C — Live Ops Active** | `LIVE-2026-CS204` | 2 active sessions | Live Ops matrix, real-time status, bonus time button |
| **D — Take the Exam Now** | `LIVE-2026-CS101` | Zero attempts, open | Full cockpit: anti-cheat, lifelines, heartbeat, auto-save |

---

## Project Structure

```
OptiExam/
|
+-- apps/
|   +-- core/
|   |   +-- management/commands/
|   |   |   +-- seed_pakistan_data.py   <- Comprehensive Pakistani demo seeder
|   |   |   +-- auto_submit_expired.py  <- Cron: auto-finalize timed-out exams
|   |   +-- middleware.py               <- TenantResolutionMiddleware
|   |   +-- mixins.py                   <- Role-gated class-based view mixins
|   |   +-- context_processors.py       <- 5 global context processors
|   |
|   +-- tenants/
|   |   +-- models.py                   <- Tenant, TenantFeatureFlag
|   |   +-- views/tenant_views.py       <- Institution CRUD, feature flags
|   |
|   +-- accounts/
|   |   +-- models.py                   <- User, UserProfile, AuditLog, Notification
|   |   +-- views/                      <- Login, profile, password management
|   |
|   +-- exams/
|   |   +-- models.py                   <- Exam, ExamSection, ExamQuestionAssignment
|   |   +-- views/
|   |       +-- blueprint_views.py      <- Multi-step exam blueprint builder
|   |       +-- roster_views.py         <- Participant enrollment and CSV import
|   |       +-- live_ops_views.py       <- Real-time candidate command center
|   |       +-- analytics_views.py      <- Score analytics and item analysis
|   |
|   +-- questions/
|   |   +-- models.py                   <- QuestionBank, Question, QuestionOption, Rubric
|   |   +-- views/
|   |       +-- bank_views.py           <- Question bank CRUD
|   |       +-- authoring_views.py      <- Multi-format question editor
|   |
|   +-- submissions/
|   |   +-- models.py                   <- ExamAttempt, AttemptAnswer, ProctoringLog
|   |   +-- views/
|   |       +-- lobby_views.py          <- Pre-exam lobby with countdown
|   |       +-- cockpit_views.py        <- Live anti-cheat exam cockpit
|   |
|   +-- grading/
|       +-- models.py                   <- GraderAllocation, QuestionScore, Moderation
|       +-- views/
|           +-- allocation_views.py     <- Batch assignment designer UI
|           +-- evaluation_views.py     <- Split-screen grading studio
|           +-- moderation_views.py     <- Chief Examiner review and override
|
+-- static/
|   +-- css/
|   |   +-- optiexam-core.css           <- Design tokens, utilities, grid system
|   |   +-- optiexam-theme.css          <- Dark/Light theme CSS variables
|   |   +-- cockpit.css                 <- Distraction-free exam cockpit UI
|   +-- js/
|   |   +-- optiexam-core.js            <- UI interactions, form guards, notifications
|   |   +-- anti-cheat-shield.js        <- Fullscreen, clipboard, DevTools blocking
|   |   +-- heartbeat-sync.js           <- 15s auto-save, offline queue, crash recovery
|   |   +-- analytics-charts.js         <- Canvas histogram and scatter plot
|   +-- fonts/                          <- Inter, Outfit, JetBrains Mono (WOFF2)
|   +-- icons/lucide-sprite.svg         <- Lucide icon bundle (100% offline)
|
+-- templates/
|   +-- base.html                       <- Base template (zero CDN)
|   +-- accounts/login.html             <- Premium 70/30 split login page
|   +-- includes/                       <- Navbar, notification bell, modals
|
+-- Doc/                                <- Full technical specification library
|   +-- PRD.md                          <- Product Requirements Document
|   +-- DFD.md                          <- Data Flow Diagrams
|   +-- models_schema.md                <- Complete ORM model reference
|   +-- api_spec.md                     <- REST API specification
|   +-- phase_01.md through phase_05.md <- Phase-by-phase implementation specs
|
+-- .env.example                        <- Environment variable template
+-- requirements.txt                    <- Production dependencies
+-- requirements-dev.txt                <- Development and test dependencies
+-- DEMO_CREDENTIALS.txt               <- Auto-generated demo user credentials
+-- manage.py
```

---

## Case Studies and Real-World Scenarios

---

### Case Study 1: NUST SEECS — Midterm Examination (CS401)

**Institution:** National University of Sciences and Technology  
**Exam:** CS401 Advanced Data Structures and Algorithms — Midterm  
**Scale:** 250 candidates | 4 sections | 90 minutes | 100 marks

**Scenario Flow:**

```
Week -2: Dr. Sarah Khan (Designer) creates exam blueprint CS401
         -> Section A: 6 MCQs (25 marks, automated grading)
         -> Section B: 4 Diagram / Multi MCQs (35 marks, automated)
         -> Section C: 2 Short answers (20 marks, manual rubrics)
         -> Section D: 1 Long system design essay (20 marks, 3 rubric criteria)
         -> Lifelines: 50:50 x2, Skip x2, Hint x2, Bookmark unlimited
         -> Anti-cheat: Fullscreen ON, max 3 tab-switches, shuffle ON

Week -1: Prof. Ahmed Bilal (Item Writer) authors all 13 questions
         -> AVL tree complexity (MCQ), Red-Black rotation (Diagram MCQ)
         -> Dijkstra negative weights (Short Answer, 5 marks)
         -> Distributed Rate Limiter design (Long Essay: Algorithm/Concurrency/Failover)

Exam Day 9:00 AM: Ali Hassan (Candidate) enters lobby
         -> Reads instructions: fullscreen warning, lifeline guide
         -> Clicks "Start Exam" -> fullscreen activates, anti-cheat shields attach
         -> Heartbeat every 15 seconds saves answers automatically to server
         -> Uses 50:50 on Q3 -> two wrong options eliminated
         -> Uses Hint on Q7 -> "AVL trees maintain strict h <= 1.44 log2(N)"
         -> Tab switch detected at 00:41:10 -> Warning 1 of 3 shown
         -> Submits at 01:22:33 -> Submission receipt with full answer summary

Post-Exam: Grader Zainab opens batch queue
         -> Sees CAND-042 (anonymized, double-blind)
         -> Split screen: LEFT (student essay), RIGHT (model answer + rubric)
         -> Awards: Algorithm 2.8/3.0, Concurrency 3.5/4.0, Failover 2.9/3.0
         -> Total subjective score: 9.2/10
         -> Finalizes -> Dr. Sarah reviews -> APPROVED

3 Days Later: Results published
         -> Ali Hassan logs in -> scorecard: 87.3 / 100, PASSED
         -> Section breakdown, grader feedback, PDF transcript downloadable
         -> Dr. Sarah views analytics: p-value=0.64 (medium), D-index=0.42 (good)
```

**Outcome:** 90-minute exam with zero data loss. 249/250 candidates submitted. 1 auto-submitted at expiry. Results published within 3 days.

---

### Case Study 2: KEMU — Clinical Physiology Spotter (MED201)

**Institution:** King Edward Medical University  
**Exam:** MED201 Clinical Physiology — Diagram Spotter

**Scenario:** A 12-lead ECG image is shown as the question body; candidates identify the occluded coronary artery.

```
Question Type  : Picture / Diagram MCQ
Image          : 12-lead ECG strip (uploaded locally to /media/)
Options        : A) LAD    B) RCA    C) LCx    D) Left Main
Correct Answer : B  (ST-elevations in II, III, aVF -> Inferior STEMI -> RCA)
Bloom's Level  : APPLY
Difficulty     : HARD
Negative Marks : -0.50 for wrong selection
```

**Candidate Experience:**
- ECG image rendered with a pinch-zoom tool inside the exam cockpit
- Candidate enlarges the image and identifies the inferior leads ST pattern
- Selects option B — server-side automated grading awards full marks instantly
- Post-exam: per-option explanation visible: "RCA supplies the inferior wall in ~85% of individuals"

---

### Case Study 3: HR Assessment Center — Corporate Python Certification

**Use Case:** Technology company conducting a Python Developer Certification for 80 candidates  
**Challenge:** No two candidates should see an identical question order; answer sharing must be prevented

**OptiExam Solution — Deterministic Candidate Seed Shuffle:**

```python
# Each candidate gets a uniquely ordered question sequence
candidate_seed    = hash(f"{candidate_id}_{exam_id}")
shuffled_questions = seeded_shuffle(question_list, candidate_seed)
shuffled_options   = seeded_shuffle(options, candidate_seed)

# Result:
# Candidate Ali Hassan:    Q-5, Q-2, Q-8, Q-1, Q-7 ...
# Candidate Fatima Zahra: Q-3, Q-7, Q-1, Q-9, Q-4 ...
# Different order. Same total marks. Same time limit.
```

**Anti-cheat layer:** DevTools shortcut (F12, Ctrl+Shift+I) intercepted -> violation logged -> Designer immediately notified in Live Ops matrix.

---

### Case Study 4: Emergency Browser Crash Recovery

**Scenario:** Candidate Usman Akbar is 35 minutes into a 60-minute exam when his browser crashes due to a power interruption.

```
T+35:00 -> Browser closes unexpectedly (power cut)
T+36:00 -> Usman reopens browser, navigates to exam URL
T+36:05 -> System detects IN_PROGRESS attempt via resume_token
T+36:05 -> Cockpit rehydrated from server (last heartbeat: Question 8 of 12)
           -> All 7 previous answers restored from AttemptAnswer records
           -> Timer reconstructed: 25 minutes remaining (server clock)
           -> Proctoring log: 0 violations recorded
T+61:00 -> Usman submits normally. Zero data loss.
```

**Zero data loss guaranteed:** Every 15-second heartbeat upserts `AttemptAnswer` records. Maximum theoretical data loss is 15 seconds of typing — never an entire exam session.

---

## Testing

```bash
# Full test suite (33 tests)
pytest apps/ -v

# With coverage report
pytest apps/ --cov=apps --cov-report=term-missing

# Specific module
pytest apps/submissions/ -v
pytest apps/grading/ -v
```

### Test Coverage Summary

| Module | Tests | Coverage Areas |
|--------|-------|----------------|
| `accounts` | 2 | Login flow, role-based redirect, audit event logging |
| `core` | 12 | Context processors, tenant isolation, RBAC mixins, zero-CDN assertion |
| `exams` | 4 | Blueprint creation, section assignment, roster import, lifeline config |
| `questions` | 5 | Question bank CRUD, all 5 formats, rubric associations, bulk import |
| `tenants` | 10 | Institution CRUD, tier filtering, feature flag toggles, audit log explorer |

```
============================= 33 passed in 15.38s =============================
```

---

## Roadmap

| Phase | Status | Deliverables |
|-------|--------|--------------|
| **Phase 1** — Core Foundation | Complete | Multi-tenancy, RBAC, auth, design system, Super Admin hub |
| **Phase 2** — Exam Authoring | Complete | Question banks, 5 formats, rubrics, blueprint builder, roster import |
| **Phase 3** — Live Exam Engine | Complete | Candidate cockpit, anti-cheat, heartbeat, crash recovery, Live Ops |
| **Phase 4** — Batched Grading | Complete | Double-blind evaluation, rubric scoring, SLA tracking, moderation |
| **Phase 5** — Analytics and Hardening | Complete | Item analysis, score distribution, psychometric charts, notifications |
| **Phase 6** — WebSocket Real-time | Planned | Django Channels: true push-based live updates replacing polling |
| **Phase 7** — Mobile Companion | Planned | Progressive Web App for candidate mobile exam experience |
| **Phase 8** — AI-Assisted Grading | Planned | LLM-assisted rubric suggestions for long essay evaluation |

---

## Author and Contact

<br/>

<div align="center">

### Built by **Zeeshan Shabbir Qureshi**

*Full-Stack Django Engineer | Assessment Platform Specialist*

<br/>

| Channel | Details |
|---------|---------|
| **Email** | [zeeshan.shabbirqureshi@gmail.com](mailto:zeeshan.shabbirqureshi@gmail.com) |
| **LinkedIn** | [linkedin.com/in/zeeshansq](https://www.linkedin.com/in/zeeshansq) |
| **WhatsApp** | [+92 315 5754436](https://wa.me/923155754436) |

<br/>

---

### Interested in OptiExam?

> Have a university, college, or corporate body that needs a purpose-built examination engine?  
> Want to license, customize, or deploy OptiExam at your institution?

**What I offer:**
- Source code licensing for institutional use
- Custom feature development (additional question types, LMS integrations, SSO)
- Deployment and infrastructure setup (on-premise or cloud)
- Staff training and full technical documentation

**Reach out:** [zeeshan.shabbirqureshi@gmail.com](mailto:zeeshan.shabbirqureshi@gmail.com)

<br/>

---

*OptiExam Assessment Platform — Engineered for rigorous, high-scale academic evaluations.*  
*Django 5.x · Python 3.12+ · Vanilla CSS · Zero CDN · 100% Offline Ready*

</div>
