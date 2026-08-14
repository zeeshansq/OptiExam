# Phase 2: Question Authoring Studio & Exam Blueprinting Hub
**Document:** `Doc/phase_02_exam_blueprint_and_question_authoring.md`  
**Project:** OptiExam Assessment Platform  
**Target Environment:** Python 3.12+ / Django 5.x / `C:\venv\envoptiexam`  
**Document Version:** 1.0.0  
**Phase Status:** Ready for Implementation (Depends on Phase 1)  

---

## 1. Phase Overview & Strategic Objectives

Phase 2 builds the core academic creation engines of OptiExam. It delivers the **Question Bank Authoring Studio** for Item Writers (supporting 5 question types, diagram uploads, Bloom's taxonomy tagging, and rubric criteria) and the **Exam Blueprinting & Roster Management Hub** for Designers (multi-step exam builder, section weightages, question assignments, lifeline configurations, and bulk CSV candidate roster imports).

```
┌────────────────────────────────────────────────────────────────────────┐
│                          PHASE 2 DELIVERABLES                          │
├────────────────────────────────────────────────────────────────────────┤
│  1. Question Bank Repository Management (`apps/questions`)             │
│  2. 5-Format Dynamic Question Authoring Studio (MCQ, Image, Short, Long)│
│  3. Model Answers, Rubric Criteria Matrix & Bloom's Taxonomy Tagging   │
│  4. Exam Blueprint Studio (`apps/exams`) with Scheduling & Anti-Cheat   │
│  5. Dynamic ExamSection Builder & Section-level Weightage Matrix       │
│  6. `ExamQuestionAssignment` Ordering & Section Attachment Engine      │
│  7. `ExamLifelineConfig` Rules Engine (Skip, 50:50, Hint, Bookmark)   │
│  8. `ExamParticipantRoster` Hub with Bulk CSV Roster Import Engine     │
│  9. Item Writer Quality Review Queue & Usage Statistics Hub            │
│  10. Automated Validation Suites (Weightage sums, MCQ parity, Roster)  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Target Component & Directory Layout

```
apps/
├── questions/
│   ├── models.py              # QuestionBank, Question, QuestionOption, QuestionRubric
│   ├── admin.py
│   ├── forms.py               # MCQQuestionForm, OptionFormSet, ShortAnswerForm,
│   │                          # LongEssayForm, RubricFormSet, QuestionFilterForm
│   ├── urls.py                # app_name = 'questions'
│   ├── views/
│   │   ├── bank_views.py      # QuestionBank list, create, edit
│   │   └── authoring_views.py # Multi-format authoring studio & review queue
│   ├── services/
│   │   └── question_service.py # create_question, duplicate_question, sync_rubrics
│   ├── selectors/
│   │   └── question_selectors.py # get_bank_questions, filter_by_taxonomy, search
│   ├── templates/questions/
│   │   ├── bank_list.html
│   │   ├── question_list.html
│   │   ├── question_form_mcq.html
│   │   ├── question_form_image_mcq.html
│   │   ├── question_form_short.html
│   │   └── question_form_essay.html
│   └── tests/
└── exams/
    ├── models.py              # Exam, ExamSection, ExamQuestionAssignment,
    │                          # ExamLifelineConfig, ExamParticipantRoster
    ├── admin.py
    ├── forms.py               # ExamForm, ExamSectionFormSet, LifelineConfigFormSet,
    │                          # RosterCSVImportForm, RosterManualAddForm, QuestionAssignForm
    ├── urls.py                # app_name = 'exams'
    ├── views/
    │   ├── blueprint_views.py # Multi-step exam creator, section builder
    │   ├── assignment_views.py# Question assignment palette & reordering
    │   └── roster_views.py    # CSV import, roster table, manual enrollment
    ├── services/
    │   ├── exam_lifecycle_service.py # create_exam_blueprint, validate_exam_integrity
    │   └── roster_service.py  # import_roster_from_csv, enroll_participant, lock_roster
    ├── selectors/
    │   └── exam_selectors.py  # get_designer_exams, get_exam_blueprint_summary
    ├── templates/exams/
    │   ├── exam_list.html
    │   ├── exam_form.html     # Multi-step blueprint builder
    │   ├── section_builder.html
    │   ├── question_assign.html
    │   ├── lifeline_config.html
    │   └── roster_hub.html    # CSV upload & candidate roster matrix
    └── tests/
```

---

## 3. Step-by-Step Implementation Tasks

### Task 2.1: Question Bank Repository (`apps/questions`)
1. Implement `QuestionBank` model scoped by `TenantModelMixin` (`name`, `code`, `subject`, `description`, `created_by`).
2. Build Question Bank listing, creation, and detail views with search and subject filtering.
3. Add question count badges and author attribution cards.

### Task 2.2: 5-Format Question Authoring Studio
1. Implement `Question`, `QuestionOption`, and `QuestionRubric` models in `apps/questions/models.py`.
2. Author dynamic formsets and views for the 5 question formats:
   * **Format A: Single-Choice MCQ (`MCQ_SINGLE`)**: Text/Math/Code prompt, 2–6 options, radio button for correct option, per-option explanation for post-exam review.
   * **Format B: Multiple-Choice MCQ (`MCQ_MULTIPLE`)**: Checkboxes for multiple correct options, partial scoring rules, negative marking per incorrect choice.
   * **Format C: Picture / Diagram-based MCQ (`IMAGE_MCQ`)**: High-resolution local image upload with thumbnail preview, zoom tool in exam preview, image or text options.
   * **Format D: Short Answer (`SHORT_ANSWER`)**: Strict word limit validator (e.g. 50–200 words), keyword matching guide for graders, rich model answer.
   * **Format E: Long Essay / Structured (`LONG_ESSAY`)**: Detailed prompt, rich model solution, and dynamic `QuestionRubricFormSet` (criteria titles, scoring descriptions, max points).
3. Add pedagogical tagging fields: `difficulty` (`EASY`, `MEDIUM`, `HARD`), `blooms_level` (`REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE`), topic tags, and `hint_text` (for Hint Token lifeline).
4. Implement `BaseOptionFormSet` validation (ensuring Single MCQ has exactly 1 correct option, Multi MCQ has ≥ 1 correct option).

### Task 2.3: Exam Blueprint Studio (`apps/exams`)
1. Implement `Exam` model with full scheduling, anti-cheating, and passing percentage attributes.
2. Implement `ExamSection` model for partitioning exams (e.g. Section A: 30 MCQs, Section B: 2 Long Essays).
3. Implement `ExamForm` and `ExamSectionFormSet` in `apps/exams/forms.py` with custom validation:
   * `start_time < end_time`
   * `duration_minutes ≤ total scheduling window`
   * Section weightages sum matching `total_marks`.
4. Build a sleek multi-step UI with interactive progress tabs:
   * Step 1: Basic Info & Schedule Window
   * Step 2: Anti-Cheating & Security Toggles
   * Step 3: Sections & Marks Distribution
   * Step 4: Lifeline Rules Configuration

### Task 2.4: Question Assignment & Section Mapping
1. Implement `ExamQuestionAssignment` model linking `ExamSection` to `Question` with custom display `order` and optional `custom_marks` override.
2. Build an interactive Question Picker:
   * Filter questions from tenant's question banks by subject, difficulty, Bloom's level, or type.
   * Add selected questions to target exam section.
   * Drag-and-drop or numeric reordering of questions.
3. Validate that all assigned questions belong to the active tenant.

### Task 2.5: Lifeline Configuration Engine
1. Implement `ExamLifelineConfig` model (`SKIP_QUESTION`, `FIFTY_FIFTY`, `HINT_TOKEN`, `BOOKMARK_FLAG`).
2. Build `ExamLifelineConfigFormSet` allowing the Designer to enable/disable each lifeline and set max allowed usages per exam.

### Task 2.6: Participant Roster Bulk Import Hub & Access Engine
1. Implement `ExamParticipantRoster` model with `candidate_index` (sequential 1, 2, 3... integer used for grader batching), `registration_number`, `status` (`ENROLLED`, `ABSENT`, `REVOKED`).
2. Build Dedicated Roster Import Page (`/{tenant_slug}/exams/{exam_id}/roster/import/`):
   * Prominent **"Download Sample Template"** buttons (`.csv` and `.xlsx`).
   * Step-by-step instructions with field requirements table (`registration_number`, `first_name`, `last_name`, `email`, `department`, `batch_year`).
   * Drag-and-drop file upload zone.
3. Build `roster_service.py` with 2-stage import pipeline:
   * **Stage 1 (Dry-Run Validate):** Parses rows, validates email format and unique registration numbers, returns 10-row preview or line-by-line error audit table.
   * **Stage 2 (Commit Ingestion):** Provisions `accounts.User` (role: `PARTICIPANT`) if new, links to `ExamParticipantRoster` with sequential `candidate_index`, logs `DataImportJob`.

### Task 2.7: Question Bank Bulk Import Hub (`apps/questions`)
1. Build Dedicated Question Bank Import Page (`/{tenant_slug}/questions/banks/{bank_id}/import/`):
   * Prominent **"Download Question Template"** buttons (`sample_questions.csv`, `sample_questions.xlsx`, `sample_questions_bundle.zip`).
   * Comprehensive guide explaining all supported columns (`question_type`, `prompt`, `points`, `negative_points`, `difficulty`, `blooms_level`, `options`, `correct_options`, `model_answer`, `rubric_criteria`).
2. Build `question_import_service.py`:
   * Supports `.csv`, `.xlsx`, and `.zip` (with `images/` directory containing diagram PNG/JPGs).
   * **Dry-Run Parser:** Validates question types, verifies option parity (e.g. Single MCQ has 1 correct option), checks image file references exist in archive.
   * **Interactive Preview Grid:** Renders first 10 parsed questions with badge indicators.
   * **Atomic Importer:** Ingests `Question`, `QuestionOption`, and `QuestionRubric` records in a single database transaction.

### Task 2.8: Sample Template Generator Engine (`apps/core/services/template_service.py`)
1. Implement dynamic file generation service delivering downloadable templates:
   * `generate_sample_roster_template(format='csv'|'xlsx')`: Includes 5 realistic sample student rows.
   * `generate_sample_question_bank_template(format='csv'|'xlsx')`: Includes 1 Single MCQ, 1 Multi MCQ, 1 Image Diagram MCQ, 1 Short Answer, and 1 Long Essay with rubric criteria.
   * `generate_sample_questions_zip_bundle()`: Packages sample CSV and 2 sample diagram images in an `images/` folder.


---

## 4. Detailed Data Models & Relationships in Phase 2

```
┌─────────────────────────────────┐
│     questions.QuestionBank      │
├─────────────────────────────────┤
│ id (PK)                         │
│ tenant_id (FK)                  │◄──┐
│ name, code, subject             │   │
└────────────────┬────────────────┘   │
                 │ 1:N                │
                 ▼                    │
┌─────────────────────────────────┐   │   ┌─────────────────────────────────┐
│       questions.Question        │   │   │       exams.ExamSection         │
├─────────────────────────────────┤   │   ├─────────────────────────────────┤
│ id (PK)                         │   │   │ id (PK)                         │
│ tenant_id (FK)                  │   │   │ exam_id (FK)                    │
│ bank_id (FK)                    │   │   │ title (VARCHAR 150)             │
│ question_type (5 types)         │   │   │ order (INT), weightage (DECIMAL)│
│ prompt (TEXT), image_asset      │   │   └────────────────┬────────────────┘
│ points, negative_points         │   │                    │ 1:N
│ difficulty, blooms_level        │   │                    ▼
│ model_answer, hint_text         │   │   ┌─────────────────────────────────┐
└───────┬─────────────────┬───────┘   │   │  exams.ExamQuestionAssignment   │
        │ 1:N             │ 1:N       │   ├─────────────────────────────────┤
        ▼                 ▼           └───┤ section_id (FK)                 │
┌───────────────┐ ┌───────────────┐       │ question_id (FK)                │
│QuestionOption │ │QuestionRubric │       │ order (INT), custom_marks       │
├───────────────┤ ├───────────────┤       └─────────────────────────────────┘
│ option_text   │ │criteria_title │
│ option_image  │ │description    │       ┌─────────────────────────────────┐
│ is_correct    │ │max_points     │       │   exams.ExamParticipantRoster   │
│ order         │ │order          │       ├─────────────────────────────────┤
└───────────────┘ └───────────────┘       │ id (PK)                         │
                                          │ exam_id (FK)                    │
                                          │ participant_id (FK User)        │
                                          │ candidate_index (INT, INDEX)    │
                                          │ registration_number (VARCHAR 50)│
                                          │ status (ENROLLED|ABSENT|REVOKED)│
                                          └─────────────────────────────────┘
```

---

## 5. UI/UX Design System Specifications for Authoring & Blueprinting

1. **Full-Screen Width Studio Architecture**:
   * Uses 100% full screen width layout (`.container`, `.container-fluid`) to provide expansive horizontal authoring space.
   * Multi-column Question Bank and Blueprint grids expand across the full viewport width.
2. **Question Authoring UI**:
   * Dynamic Alpine.js or Vanilla JS formset manager for adding/removing options without page refresh.
   * Wide split preview card updating live as Item Writer types.
   * Model answer accordion with clear "Confidential to Graders" warning badge.
3. **Exam Blueprint UI**:
   * Multi-step wizard with visual progress breadcrumb (`Details → Security → Sections & Questions → Lifelines → Roster`).
   * Visual weightage distribution summary bar and full-width Question Bank picker table.

   * Interactive CSV dropzone with instantaneous row count validation.

---

## 6. Verification & Automated Test Plan

### Test Suite Execution
```powershell
& "C:\venv\envoptiexam\Scripts\python.exe" -m pytest apps/questions/tests apps/exams/tests -v --cov=apps/questions --cov=apps/exams
```

### Key Test Cases:
1. `test_mcq_single_validation_exact_one_correct`: Rejects submission if 0 or 2 options marked correct.
2. `test_mcq_multiple_validation_at_least_one_correct`: Passes when 2 options marked correct.
3. `test_long_essay_rubric_sum_validation`: Validates rubric criteria points sum matches total question points.
4. `test_csv_roster_import_sequential_indexing`: Validates 50 imported candidates receive `candidate_index` 1 through 50 without gaps.
5. `test_exam_scheduling_window_validation`: Rejects exam where `duration_minutes` > `end_time - start_time`.
6. `test_question_assignment_tenant_isolation`: Prevents assigning a question from Tenant A to an exam in Tenant B.

---

## 7. Definition of Done (DoD) for Phase 2
* [ ] Item Writers can create, edit, and preview all 5 question types with model answers and rubrics.
* [ ] Image uploads for diagram MCQs work offline and store files locally in `media/questions/diagrams/`.
* [ ] Designers can configure complete exam blueprints, partition into sections, and assign questions with custom order.
* [ ] Designers can upload a CSV participant roster and verify imported candidates with sequential indices.
* [ ] All unit and validation tests pass with ≥ 90% code coverage.
