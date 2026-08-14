from typing import Optional
from django.db.models import QuerySet, Q, Count
from apps.exams.models import Exam, ExamParticipantRoster, ExamSection
from apps.tenants.models import Tenant

def get_tenant_exams(
    tenant: Tenant,
    search_query: Optional[str] = None,
    subject: Optional[str] = None,
    status_filter: Optional[str] = None,
    sort_by: str = '-start_time'
) -> QuerySet[Exam]:
    """
    Returns exams for a tenant with optional filtering.
    """
    qs = Exam.objects.for_tenant(tenant).annotate(
        total_enrolled=Count('roster_entries', distinct=True),
        total_sections=Count('sections', distinct=True)
    )

    if search_query:
        qs = qs.filter(
            Q(title__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if subject:
        qs = qs.filter(subject__icontains=subject)

    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'published':
        qs = qs.filter(results_published=True)
    elif status_filter == 'draft':
        qs = qs.filter(is_active=False)

    allowed_sorts = [
        'title', '-title', 'code', '-code', 'start_time', '-start_time',
        'duration_minutes', '-duration_minutes', 'total_marks', '-total_marks'
    ]
    if sort_by in allowed_sorts:
        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by('-start_time')

    return qs


def get_exam_roster(
    exam: Exam,
    search_query: Optional[str] = None,
    status: Optional[str] = None
) -> QuerySet[ExamParticipantRoster]:
    """
    Returns candidate roster for an exam ordered by sequential candidate_index.
    """
    qs = ExamParticipantRoster.objects.filter(exam=exam).select_related('participant', 'participant__profile')

    if search_query:
        qs = qs.filter(
            Q(participant__first_name__icontains=search_query) |
            Q(participant__last_name__icontains=search_query) |
            Q(participant__email__icontains=search_query) |
            Q(registration_number__icontains=search_query)
        )

    if status:
        qs = qs.filter(status=status)

    return qs.order_by('candidate_index')
