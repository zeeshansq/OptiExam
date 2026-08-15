from typing import Optional, Dict, Any, List
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.exams.models import Exam, ExamSection, ExamQuestionAssignment, ExamLifelineConfig
from apps.questions.models import Question
from apps.tenants.models import Tenant

@transaction.atomic
def create_exam_blueprint(
    tenant: Tenant,
    title: str,
    code: str,
    subject: str,
    start_time,
    end_time,
    duration_minutes: int = 60,
    total_marks: Decimal = Decimal('100.0'),
    passing_percentage: Decimal = Decimal('40.0'),
    instructions: str = '',
    created_by = None,
    sections_data: Optional[List[Dict[str, Any]]] = None
) -> Exam:
    """
    Creates an Exam blueprint, sets up default lifeline configs, and creates sections.
    """
    exam = Exam.objects.create(
        tenant=tenant,
        title=title,
        code=code,
        subject=subject,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        total_marks=total_marks,
        passing_percentage=passing_percentage,
        instructions=instructions,
        created_by=created_by,
        is_active=True
    )

    # Initialize standard lifelines
    for lt in ExamLifelineConfig.LifelineType.values:
        ExamLifelineConfig.objects.create(
            exam=exam,
            lifeline_type=lt,
            is_enabled=True,
            max_allowed=1
        )

    # Create initial section if provided or default Section A
    if sections_data:
        for idx, sec in enumerate(sections_data):
            ExamSection.objects.create(
                exam=exam,
                title=sec.get('title', f"Section {chr(65+idx)}"),
                description=sec.get('description', ''),
                order=sec.get('order', idx + 1),
                weightage=Decimal(str(sec.get('weightage', 100.0)))
            )
    else:
        ExamSection.objects.create(
            exam=exam,
            title="Section A — General Examination",
            order=1,
            weightage=Decimal('100.0')
        )

    return exam


@transaction.atomic
def assign_question_to_section(
    section: ExamSection,
    question: Question,
    order: Optional[int] = None,
    custom_marks: Optional[Decimal] = None,
    is_reserve: bool = False
) -> ExamQuestionAssignment:
    """
    Assigns a question to an exam section with tenant verification.
    Can be assigned as an active question (is_reserve=False) or a reserve pool item (is_reserve=True).
    """
    if section.exam.tenant != question.tenant:
        raise ValidationError("Cannot assign question from a different institution.")

    if order is None:
        max_order = section.assignments.all().count()
        order = max_order + 1

    assignment, _ = ExamQuestionAssignment.objects.update_or_create(
        section=section,
        question=question,
        defaults={
            'order': order,
            'custom_marks': custom_marks,
            'is_reserve': is_reserve
        }
    )
    return assignment



@transaction.atomic
def remove_question_from_section(section: ExamSection, question: Question) -> None:
    """
    Removes a question assignment from an exam section.
    """
    ExamQuestionAssignment.objects.filter(section=section, question=question).delete()
