from typing import Optional
from django.db.models import QuerySet, Q, Count
from apps.questions.models import QuestionBank, Question
from apps.tenants.models import Tenant

def get_tenant_question_banks(
    tenant: Tenant,
    search_query: Optional[str] = None,
    subject: Optional[str] = None
) -> QuerySet[QuestionBank]:
    """
    Returns question banks for a tenant with optional filtering.
    """
    qs = QuestionBank.objects.for_tenant(tenant).annotate(
        total_questions=Count('questions')
    )

    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if subject:
        qs = qs.filter(subject__icontains=subject)

    return qs.order_by('-created_at')


def get_bank_questions(
    bank: QuestionBank,
    search_query: Optional[str] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    blooms_level: Optional[str] = None,
    sort_by: str = '-created_at'
) -> QuerySet[Question]:
    """
    Returns questions belonging to a specific question bank.
    """
    qs = Question.objects.filter(bank=bank).prefetch_related('options', 'rubrics')

    if search_query:
        qs = qs.filter(
            Q(prompt__icontains=search_query) |
            Q(topic_tags__icontains=search_query) |
            Q(model_answer__icontains=search_query)
        )

    if question_type:
        qs = qs.filter(question_type=question_type)

    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    if blooms_level:
        qs = qs.filter(blooms_level=blooms_level)

    allowed_sorts = ['prompt', '-prompt', 'points', '-points', 'difficulty', '-difficulty', 'created_at', '-created_at']
    if sort_by in allowed_sorts:
        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by('-created_at')

    return qs
