import pytest
from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.tenants.models import Tenant
from apps.accounts.models import UserRole
from apps.questions.models import QuestionBank, Question, QuestionOption, QuestionRubric
from apps.questions.services.question_service import create_question, duplicate_question
from apps.questions.services.question_import_service import parse_and_validate_question_rows, commit_question_import
from apps.core.services.template_service import generate_sample_question_bank_template

User = get_user_model()

@pytest.fixture
def sample_tenant(db):
    return Tenant.objects.create(
        name="Apex Institute of Technology",
        slug="apex",
        tier=Tenant.Tier.PROFESSIONAL,
        is_active=True
    )

@pytest.fixture
def other_tenant(db):
    return Tenant.objects.create(
        name="Global Medical College",
        slug="gmc",
        tier=Tenant.Tier.ENTERPRISE,
        is_active=True
    )

@pytest.fixture
def item_writer_user(db, sample_tenant):
    return User.objects.create_user(
        username="writer_apex",
        email="writer@apex.edu",
        password="WriterPass2026!",
        tenant=sample_tenant,
        role=UserRole.ITEM_WRITER
    )

@pytest.mark.django_db
class TestQuestionBankAndModels:
    def test_question_bank_scoping_and_creation(self, sample_tenant, other_tenant, item_writer_user):
        bank_apex = QuestionBank.objects.create(
            tenant=sample_tenant,
            name="Computer Science 101",
            code="CS101",
            subject="Computer Science",
            created_by=item_writer_user
        )
        bank_gmc = QuestionBank.objects.create(
            tenant=other_tenant,
            name="Anatomy & Physiology",
            code="MED-ANAT",
            subject="Medicine"
        )

        apex_banks = QuestionBank.objects.for_tenant(sample_tenant)
        assert bank_apex in apex_banks
        assert bank_gmc not in apex_banks
        assert bank_apex.question_count == 0

    def test_create_mcq_single_and_multiple_questions(self, sample_tenant, item_writer_user):
        bank = QuestionBank.objects.create(
            tenant=sample_tenant,
            name="Data Structures",
            subject="Computer Science",
            created_by=item_writer_user
        )

        # 1. Single Choice MCQ
        q_single = create_question(
            bank=bank,
            prompt="What is the worst-case time complexity of QuickSort?",
            question_type=Question.QuestionType.MCQ_SINGLE,
            points=Decimal('2.0'),
            difficulty=Question.Difficulty.HARD,
            blooms_level=Question.BloomsLevel.ANALYZE,
            options_data=[
                {'option_text': 'O(n log n)', 'is_correct': False},
                {'option_text': 'O(n^2)', 'is_correct': True},
                {'option_text': 'O(n)', 'is_correct': False},
            ]
        )
        assert q_single.is_mcq is True
        assert q_single.is_subjective is False
        assert q_single.options.count() == 3
        assert q_single.options.filter(is_correct=True).count() == 1

        # 2. Multi Choice MCQ
        q_multi = create_question(
            bank=bank,
            prompt="Select all linear data structures:",
            question_type=Question.QuestionType.MCQ_MULTIPLE,
            points=Decimal('3.0'),
            options_data=[
                {'option_text': 'Array', 'is_correct': True},
                {'option_text': 'Binary Tree', 'is_correct': False},
                {'option_text': 'Queue', 'is_correct': True},
            ]
        )
        assert q_multi.options.filter(is_correct=True).count() == 2

    def test_create_long_essay_with_rubrics_and_duplicate(self, sample_tenant, item_writer_user):
        bank = QuestionBank.objects.create(
            tenant=sample_tenant,
            name="Advanced Algorithms",
            subject="Computer Science"
        )

        q_essay = create_question(
            bank=bank,
            prompt="Explain the Bellman-Ford shortest path algorithm in detail.",
            question_type=Question.QuestionType.LONG_ESSAY,
            points=Decimal('10.0'),
            model_answer="Initialization d(s)=0, relaxation over |V|-1 iterations, negative cycle check.",
            rubrics_data=[
                {'criteria_title': 'Algorithm Principles', 'max_points': Decimal('4.0')},
                {'criteria_title': 'Edge Relaxation Mechanics', 'max_points': Decimal('3.0')},
                {'criteria_title': 'Negative Cycle Detection', 'max_points': Decimal('3.0')},
            ]
        )
        assert q_essay.is_subjective is True
        assert q_essay.rubrics.count() == 3

        # Test Question Duplication Service
        cloned = duplicate_question(q_essay)
        assert cloned.pk != q_essay.pk
        assert cloned.prompt.startswith("[Copy]")
        assert cloned.rubrics.count() == 3


@pytest.mark.django_db
class TestQuestionBulkImportAndTemplates:
    def test_sample_question_bank_template_generator(self):
        csv_bytes, content_type, filename = generate_sample_question_bank_template(format_type='csv')
        assert content_type == 'text/csv'
        assert filename == 'sample_question_bank.csv'
        assert b'question_type,prompt,points' in csv_bytes
        assert b'MCQ_SINGLE' in csv_bytes
        assert b'LONG_ESSAY' in csv_bytes

    def test_two_stage_question_import_pipeline(self, sample_tenant, item_writer_user):
        bank = QuestionBank.objects.create(
            tenant=sample_tenant,
            name="Physics 101",
            subject="Physics"
        )

        csv_content = (
            "question_type,prompt,points,negative_points,difficulty,blooms_level,topic_tags,options,correct_options,model_answer,hint_text,rubric_criteria\n"
            "MCQ_SINGLE,What is the SI unit of force?,1.0,0.25,EASY,REMEMBER,mechanics,A) Joule | B) Newton | C) Pascal,B,1 Newton = 1 kg m/s^2,Named after Isaac Newton,\n"
            "SHORT_ANSWER,State Ohm's Law and its mathematical formula.,4.0,0.0,MEDIUM,UNDERSTAND,circuits,,,V = I * R where V is voltage,Consider linear conductors,\n"
        ).encode('utf-8')

        # Stage 1: Dry-Run Validation
        stage1_result = parse_and_validate_question_rows(csv_content, 'physics_bank.csv')
        assert stage1_result['valid'] is True
        assert stage1_result['total_rows'] == 2
        assert stage1_result['valid_count'] == 2
        assert len(stage1_result['preview_rows']) == 2
        assert len(stage1_result['errors']) == 0

        # Stage 2: Commit Ingestion
        job = commit_question_import(
            bank=bank,
            valid_rows=stage1_result['valid_rows'],
            user=item_writer_user,
            source_filename='physics_bank.csv'
        )
        assert job.successful_rows == 2
        assert bank.questions.count() == 2

        q_single = bank.questions.get(question_type=Question.QuestionType.MCQ_SINGLE)
        assert q_single.options.count() == 3
        assert q_single.options.get(is_correct=True).option_text == 'Newton'
