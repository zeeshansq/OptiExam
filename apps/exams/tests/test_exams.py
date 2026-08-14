import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant
from apps.accounts.models import UserRole
from apps.questions.models import QuestionBank, Question
from apps.exams.models import Exam, ExamSection, ExamQuestionAssignment, ExamLifelineConfig, ExamParticipantRoster
from apps.exams.services.exam_lifecycle_service import (
    create_exam_blueprint,
    assign_question_to_section,
    remove_question_from_section
)
from apps.exams.services.roster_service import (
    parse_and_validate_roster_rows,
    commit_roster_import
)
from apps.core.services.template_service import generate_sample_roster_template

User = get_user_model()

@pytest.fixture
def exam_tenant(db):
    return Tenant.objects.create(
        name="National Engineering College",
        slug="nec",
        tier=Tenant.Tier.ENTERPRISE,
        is_active=True
    )

@pytest.fixture
def other_tenant(db):
    return Tenant.objects.create(
        name="Apex Institute",
        slug="apex-alt",
        tier=Tenant.Tier.STARTER,
        is_active=True
    )

@pytest.fixture
def designer_user(db, exam_tenant):
    return User.objects.create_user(
        username="designer_nec",
        email="designer@nec.edu",
        password="DesignerPass2026!",
        tenant=exam_tenant,
        role=UserRole.DESIGNER
    )

@pytest.mark.django_db
class TestExamBlueprintAndLifecycle:
    def test_exam_blueprint_creation_and_lifelines(self, exam_tenant, designer_user):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=3)

        exam = create_exam_blueprint(
            tenant=exam_tenant,
            title="Algorithms Midterm Exam",
            code="CS201-MID-2026",
            subject="Computer Science",
            start_time=start,
            end_time=end,
            duration_minutes=90,
            total_marks=Decimal('100.0'),
            passing_percentage=Decimal('45.0'),
            instructions="All work must be strictly individual.",
            created_by=designer_user,
            sections_data=[
                {'title': 'Section A: Objective MCQs', 'weightage': 40.0, 'order': 1},
                {'title': 'Section B: Structured Essays', 'weightage': 60.0, 'order': 2},
            ]
        )

        assert exam.sections.count() == 2
        assert exam.lifeline_configs.count() == 4
        assert exam.lifeline_configs.filter(is_enabled=True).count() == 4
        assert exam.total_assigned_questions == 0
        assert exam.total_enrolled_candidates == 0

    def test_question_assignment_to_exam_section(self, exam_tenant, designer_user, other_tenant):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(hours=2)

        exam = create_exam_blueprint(
            tenant=exam_tenant,
            title="Physics Final",
            code="PHY101-FINAL",
            subject="Physics",
            start_time=start,
            end_time=end,
            created_by=designer_user
        )
        section_a = exam.sections.first()

        bank_nec = QuestionBank.objects.create(
            tenant=exam_tenant,
            name="NEC Physics Bank",
            subject="Physics"
        )
        q_valid = Question.objects.create(
            tenant=exam_tenant,
            bank=bank_nec,
            prompt="What is Snell's law?",
            question_type=Question.QuestionType.SHORT_ANSWER,
            points=Decimal('5.0')
        )

        assignment = assign_question_to_section(section_a, q_valid, order=1, custom_marks=Decimal('6.0'))
        assert assignment.order == 1
        assert assignment.effective_marks == Decimal('6.0')
        assert section_a.assignments.count() == 1

        # Test Removal
        remove_question_from_section(section_a, q_valid)
        assert section_a.assignments.count() == 0


@pytest.mark.django_db
class TestRosterTwoStageImportAndIndexSequence:
    def test_sample_roster_template_generator(self):
        csv_bytes, content_type, filename = generate_sample_roster_template(format_type='csv')
        assert content_type == 'text/csv'
        assert filename == 'sample_participant_roster.csv'
        assert b'registration_number,first_name,last_name,email,department,batch_year' in csv_bytes
        assert b'REG-2026-001' in csv_bytes

    def test_two_stage_roster_import_pipeline(self, exam_tenant, designer_user):
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(hours=4)

        exam = create_exam_blueprint(
            tenant=exam_tenant,
            title="Data Mining Assessment",
            code="CS401-DM",
            subject="Computer Science",
            start_time=start,
            end_time=end,
            created_by=designer_user
        )

        csv_content = (
            "registration_number,first_name,last_name,email,department,batch_year\n"
            "CS-2026-001,Tariq,Javed,tariq@student.nec.edu,Computer Science,2026\n"
            "CS-2026-002,Sara,Ahmed,sara@student.nec.edu,Software Engineering,2026\n"
            "CS-2026-003,Zain,Abbas,zain@student.nec.edu,Data Science,2025\n"
        ).encode('utf-8')

        # Stage 1: Dry-Run Validation
        stage1_result = parse_and_validate_roster_rows(csv_content, 'roster_cs.csv')
        assert stage1_result['valid'] is True
        assert stage1_result['total_rows'] == 3
        assert stage1_result['valid_count'] == 3
        assert len(stage1_result['preview_rows']) == 3
        assert len(stage1_result['errors']) == 0

        # Stage 2: Commit Ingestion
        job = commit_roster_import(
            exam=exam,
            valid_rows=stage1_result['valid_rows'],
            user=designer_user,
            source_filename='roster_cs.csv'
        )
        assert job.successful_rows == 3
        assert exam.roster_entries.count() == 3

        # Verify candidate_index sequence 1, 2, 3...
        indices = list(exam.roster_entries.order_by('candidate_index').values_list('candidate_index', flat=True))
        assert indices == [1, 2, 3]

        # Verify created Participant accounts
        p1 = User.objects.get(email="tariq@student.nec.edu")
        assert p1.role == UserRole.PARTICIPANT
        assert p1.profile.registration_number == "CS-2026-001"
