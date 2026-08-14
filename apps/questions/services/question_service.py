from typing import Optional, Dict, Any, List
from decimal import Decimal
from django.db import transaction
from apps.questions.models import QuestionBank, Question, QuestionOption, QuestionRubric
from apps.tenants.models import Tenant

@transaction.atomic
def create_question(
    bank: QuestionBank,
    prompt: str,
    question_type: str,
    points: Decimal = Decimal('1.0'),
    negative_points: Decimal = Decimal('0.0'),
    difficulty: str = Question.Difficulty.MEDIUM,
    blooms_level: str = Question.BloomsLevel.REMEMBER,
    topic_tags: str = '',
    model_answer: str = '',
    hint_text: str = '',
    image_asset = None,
    created_by = None,
    options_data: Optional[List[Dict[str, Any]]] = None,
    rubrics_data: Optional[List[Dict[str, Any]]] = None
) -> Question:
    """
    Creates a new question with attached choices or rubric criteria atomically.
    """
    question = Question.objects.create(
        tenant=bank.tenant,
        bank=bank,
        prompt=prompt,
        question_type=question_type,
        points=points,
        negative_points=negative_points,
        difficulty=difficulty,
        blooms_level=blooms_level,
        topic_tags=topic_tags,
        model_answer=model_answer,
        hint_text=hint_text,
        image_asset=image_asset,
        created_by=created_by
    )

    if options_data and question.is_mcq:
        for idx, opt in enumerate(options_data):
            QuestionOption.objects.create(
                question=question,
                option_text=opt.get('option_text', ''),
                is_correct=opt.get('is_correct', False),
                order=opt.get('order', idx),
                explanation=opt.get('explanation', '')
            )

    if rubrics_data and question.is_subjective:
        for idx, rub in enumerate(rubrics_data):
            QuestionRubric.objects.create(
                question=question,
                criteria_title=rub.get('criteria_title', ''),
                description=rub.get('description', ''),
                max_points=Decimal(str(rub.get('max_points', 1.0))),
                order=rub.get('order', idx)
            )

    return question


@transaction.atomic
def duplicate_question(question: Question, target_bank: Optional[QuestionBank] = None) -> Question:
    """
    Duplicates an existing question with all its options or rubrics into a target bank.
    """
    bank = target_bank or question.bank
    cloned_q = Question.objects.create(
        tenant=bank.tenant,
        bank=bank,
        prompt=f"[Copy] {question.prompt}",
        question_type=question.question_type,
        points=question.points,
        negative_points=question.negative_points,
        difficulty=question.difficulty,
        blooms_level=question.blooms_level,
        topic_tags=question.topic_tags,
        model_answer=question.model_answer,
        hint_text=question.hint_text,
        image_asset=question.image_asset,
        created_by=question.created_by
    )

    for opt in question.options.all():
        QuestionOption.objects.create(
            question=cloned_q,
            option_text=opt.option_text,
            is_correct=opt.is_correct,
            order=opt.order,
            explanation=opt.explanation
        )

    for rub in question.rubrics.all():
        QuestionRubric.objects.create(
            question=cloned_q,
            criteria_title=rub.criteria_title,
            description=rub.description,
            max_points=rub.max_points,
            order=rub.order
        )

    return cloned_q
