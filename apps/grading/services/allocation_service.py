from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.exams.models import Exam, ExamSection
from apps.grading.models import GraderAllocation
from apps.accounts.models import User, UserRole


@transaction.atomic
def create_grader_allocation(
    exam: Exam,
    grader: User,
    candidate_range_start: int,
    candidate_range_end: int,
    sla_deadline: Optional[timezone.datetime] = None,
    section_scope: Optional[ExamSection] = None
) -> GraderAllocation:
    """
    Allocates a sequential candidate index range to a designated examiner.
    Validates range logic and grader tenant association.
    """
    if candidate_range_end < candidate_range_start:
        raise ValidationError("Candidate range end must be greater than or equal to start.")

    if grader.tenant != exam.tenant and not grader.is_super_admin():
        raise ValidationError("Selected examiner does not belong to this institution.")

    # Check for overlapping allocation for same exam & section
    overlapping = GraderAllocation.objects.filter(
        exam=exam,
        section_scope=section_scope,
        candidate_range_start__lte=candidate_range_end,
        candidate_range_end__gte=candidate_range_start
    )
    if overlapping.exists():
        raise ValidationError(f"Candidate range #{candidate_range_start:03d}–#{candidate_range_end:03d} overlaps with existing allocation.")

    allocation = GraderAllocation.objects.create(
        tenant=exam.tenant,
        exam=exam,
        grader=grader,
        section_scope=section_scope,
        candidate_range_start=candidate_range_start,
        candidate_range_end=candidate_range_end,
        sla_deadline=sla_deadline,
        status=GraderAllocation.Status.PENDING
    )
    return allocation
