import math
from decimal import Decimal
from typing import Dict, Any, List
from django.db.models import Avg, Max, Min, StdDev, Count
from apps.exams.models import Exam, ExamParticipantRoster, ExamSection, ExamQuestionAssignment
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import GradeModeration, QuestionScore
from apps.questions.models import Question


def compute_cohort_metrics(exam: Exam) -> Dict[str, Any]:
    """
    Computes complete statistical cohort analytics for an examination.
    """
    total_registered = ExamParticipantRoster.objects.filter(exam=exam).count()
    attempts = list(
        ExamAttempt.objects.filter(exam=exam, is_simulation=False)
        .exclude(status=ExamAttempt.Status.IN_PROGRESS)
        .select_related('grade_moderation')
    )
    total_attempted = len(attempts)
    absent_count = max(0, total_registered - total_attempted)

    if total_attempted == 0:
        return {
            'total_registered': total_registered,
            'total_attempted': 0,
            'absent_count': absent_count,
            'pass_count': 0,
            'fail_count': 0,
            'pass_rate': 0.0,
            'average_score': 0.0,
            'median_score': 0.0,
            'highest_score': 0.0,
            'lowest_score': 0.0,
            'grade_histogram': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0},
            'section_averages': []
        }

    scores = []
    pass_count = 0
    grade_histogram = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    exam_total = float(exam.total_marks) or 100.0

    for att in attempts:
        score = 0.0
        if hasattr(att, 'grade_moderation') and att.grade_moderation.total_final_score is not None:
            score = float(att.grade_moderation.total_final_score)
            if att.grade_moderation.is_passed:
                pass_count += 1
        scores.append(score)

        pct = (score / exam_total) * 100.0
        if pct >= 80.0:
            grade_histogram['A'] += 1
        elif pct >= 70.0:
            grade_histogram['B'] += 1
        elif pct >= 60.0:
            grade_histogram['C'] += 1
        elif pct >= 50.0:
            grade_histogram['D'] += 1
        else:
            grade_histogram['F'] += 1

    scores.sort()
    avg_score = sum(scores) / total_attempted
    mid = total_attempted // 2
    median_score = (scores[mid] if total_attempted % 2 != 0 else (scores[mid - 1] + scores[mid]) / 2.0)
    pass_rate = (pass_count / total_attempted) * 100.0

    # Section-wise Averages
    sections = ExamSection.objects.filter(exam=exam).order_by('order')
    section_averages = []
    for sec in sections:
        sec_q_ids = ExamQuestionAssignment.objects.filter(section=sec).values_list('question_id', flat=True)
        sec_answers = AttemptAnswer.objects.filter(
            attempt__in=attempts,
            question_id__in=sec_q_ids,
            marks_awarded__isnull=False
        )
        sec_avg = sec_answers.aggregate(Avg('marks_awarded'))['marks_awarded__avg'] or 0.0
        section_averages.append({
            'section_title': sec.title,
            'average_score': float(round(sec_avg, 2))
        })

    return {
        'total_registered': total_registered,
        'total_attempted': total_attempted,
        'absent_count': absent_count,
        'pass_count': pass_count,
        'fail_count': total_attempted - pass_count,
        'pass_rate': round(pass_rate, 2),
        'average_score': round(avg_score, 2),
        'median_score': round(median_score, 2),
        'highest_score': round(max(scores), 2),
        'lowest_score': round(min(scores), 2),
        'grade_histogram': grade_histogram,
        'section_averages': section_averages
    }


def compute_item_analysis(exam: Exam) -> List[Dict[str, Any]]:
    """
    Pedagogical Item Analysis Engine:
    Computes Difficulty Index (p-value), Discrimination Index (r-value),
    and Bloom's level breakdown for every question in the exam.
    """
    attempts = list(
        ExamAttempt.objects.filter(exam=exam, is_simulation=False)
        .exclude(status=ExamAttempt.Status.IN_PROGRESS)
        .select_related('grade_moderation')
    )
    total_candidates = len(attempts)
    if total_candidates == 0:
        return []

    # Sort candidates by total score
    def get_score(att):
        if hasattr(att, 'grade_moderation') and att.grade_moderation.total_final_score is not None:
            return float(att.grade_moderation.total_final_score)
        return 0.0

    sorted_attempts = sorted(attempts, key=get_score, reverse=True)
    top_cutoff = max(1, int(round(total_candidates * 0.27)))
    bottom_cutoff = top_cutoff
    top_attempts = sorted_attempts[:top_cutoff]
    bottom_attempts = sorted_attempts[-bottom_cutoff:]

    assignments = ExamQuestionAssignment.objects.filter(section__exam=exam).select_related('question').order_by('order')
    items_data = []

    for a in assignments:
        q = a.question
        if not q:
            continue

        answers = list(AttemptAnswer.objects.filter(attempt__in=attempts, question=q, marks_awarded__isnull=False))
        answered_count = len(answers)
        if answered_count == 0:
            continue

        correct_count = sum(1 for ans in answers if ans.marks_awarded and ans.marks_awarded >= (q.points * Decimal('0.5')))
        p_value = correct_count / answered_count

        # Discrimination Index
        top_ans = AttemptAnswer.objects.filter(attempt__in=top_attempts, question=q, marks_awarded__isnull=False)
        top_correct = sum(1 for ans in top_ans if ans.marks_awarded and ans.marks_awarded >= (q.points * Decimal('0.5')))
        p_top = (top_correct / len(top_ans)) if top_ans.exists() else 0.0

        bot_ans = AttemptAnswer.objects.filter(attempt__in=bottom_attempts, question=q, marks_awarded__isnull=False)
        bot_correct = sum(1 for ans in bot_ans if ans.marks_awarded and ans.marks_awarded >= (q.points * Decimal('0.5')))
        p_bot = (bot_correct / len(bot_ans)) if bot_ans.exists() else 0.0

        d_index = p_top - p_bot

        # Qualitative tags
        if p_value < 0.3:
            diff_label = 'Hard'
            diff_badge = 'badge-danger'
        elif p_value <= 0.7:
            diff_label = 'Moderate'
            diff_badge = 'badge-warning'
        else:
            diff_label = 'Easy'
            diff_badge = 'badge-success'

        if d_index >= 0.4:
            disc_label = 'Excellent'
            disc_badge = 'badge-success'
        elif d_index >= 0.2:
            disc_label = 'Acceptable'
            disc_badge = 'badge-primary'
        else:
            disc_label = 'Poor / Review'
            disc_badge = 'badge-danger'

        items_data.append({
            'question_id': q.id,
            'prompt': q.prompt[:80],
            'question_type': q.get_question_type_display(),
            'blooms_level': q.get_blooms_level_display(),
            'points': float(q.points),
            'p_value': round(p_value, 2),
            'difficulty_label': diff_label,
            'difficulty_badge': diff_badge,
            'd_index': round(d_index, 2),
            'discrimination_label': disc_label,
            'discrimination_badge': disc_badge
        })

    return items_data
