from typing import List, Dict, Any, Optional
from apps.exams.models import Exam, ExamParticipantRoster
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import GraderAllocation, QuestionScore, GradeModeration


def get_grader_allocations(grader, tenant=None) -> List[GraderAllocation]:
    """
    Returns all active batches allocated to the grader.
    """
    qs = GraderAllocation.objects.filter(grader=grader).select_related('exam', 'section_scope')
    if tenant:
        qs = qs.filter(tenant=tenant)
    return list(qs)


def get_batch_candidate_queue(allocation: GraderAllocation) -> List[Dict[str, Any]]:
    """
    Retrieves the double-blind candidate queue for an allocated batch range.
    """
    exam = allocation.exam
    roster_entries = ExamParticipantRoster.objects.filter(
        exam=exam,
        candidate_index__gte=allocation.candidate_range_start,
        candidate_index__lte=allocation.candidate_range_end
    ).select_related('participant')

    queue = []
    for entry in roster_entries:
        attempt = ExamAttempt.objects.filter(
            exam=exam,
            participant=entry.participant,
            is_simulation=False
        ).first()

        # Check subjective answers grading progress
        if attempt:
            subjective_answers = AttemptAnswer.objects.filter(
                attempt=attempt,
                question__question_type__in=['SHORT_ANSWER', 'LONG_ESSAY']
            )
            total_subj = subjective_answers.count()
            graded_subj = subjective_answers.filter(is_graded=True).count()
            has_draft = QuestionScore.objects.filter(answer__in=subjective_answers, is_draft=True).exists()

            if total_subj == 0:
                grade_status = 'NO_SUBJECTIVE'
            elif graded_subj == total_subj:
                grade_status = 'COMPLETED'
            elif has_draft or graded_subj > 0:
                grade_status = 'IN_PROGRESS'
            else:
                grade_status = 'PENDING'
        else:
            total_subj = 0
            graded_subj = 0
            grade_status = 'NOT_STARTED'

        queue.append({
            'candidate_index': entry.candidate_index,
            'blind_code': f"CAND-{entry.candidate_index:04d}",
            'attempt': attempt,
            'total_subjective': total_subj,
            'graded_subjective': graded_subj,
            'grade_status': grade_status
        })

    return queue
