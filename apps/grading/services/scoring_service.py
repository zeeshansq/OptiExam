from decimal import Decimal
from typing import Dict, Any
from django.db import transaction
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.questions.models import Question, QuestionOption
from apps.grading.models import QuestionScore, GradeModeration


@transaction.atomic
def auto_grade_mcq_attempt(attempt: ExamAttempt) -> Decimal:
    """
    Automated MCQ Evaluation Engine:
    Evaluates Single Choice, Multiple Choice, and Diagram MCQs immediately upon attempt submission.
    Awards positive marks for correct selections and applies negative penalty points where configured.
    """
    total_mcq_score = Decimal('0.00')
    answers = AttemptAnswer.objects.filter(attempt=attempt).select_related('question').prefetch_related('selected_options', 'question__options')

    for ans in answers:
        q = ans.question
        if not q.is_mcq:
            continue

        # If candidate skipped question -> 0 marks
        if ans.is_skipped:
            ans.marks_awarded = Decimal('0.00')
            ans.is_graded = True
            ans.save(update_fields=['marks_awarded', 'is_graded'])
            continue

        selected_ids = set(ans.selected_options.values_list('id', flat=True))
        correct_ids = set(q.options.filter(is_correct=True).values_list('id', flat=True))

        if not selected_ids:
            # Unanswered
            ans.marks_awarded = Decimal('0.00')
            ans.is_graded = True
            ans.save(update_fields=['marks_awarded', 'is_graded'])
            continue

        if q.question_type in (Question.QuestionType.MCQ_SINGLE, Question.QuestionType.IMAGE_MCQ):
            if selected_ids == correct_ids:
                awarded = Decimal(str(q.points))
            else:
                awarded = Decimal('-' + str(q.negative_points)) if q.negative_points > 0 else Decimal('0.00')
        elif q.question_type == Question.QuestionType.MCQ_MULTIPLE:
            # Multiple Choice MCQ: All correct required for full points
            if selected_ids == correct_ids:
                awarded = Decimal(str(q.points))
            else:
                # Deduct negative penalty if incorrect option was selected
                has_incorrect_selected = bool(selected_ids - correct_ids)
                if has_incorrect_selected and q.negative_points > 0:
                    awarded = Decimal('-' + str(q.negative_points))
                else:
                    awarded = Decimal('0.00')
        else:
            awarded = Decimal('0.00')

        ans.marks_awarded = awarded
        ans.is_graded = True
        ans.save(update_fields=['marks_awarded', 'is_graded'])
        total_mcq_score += awarded

        # Upsert QuestionScore
        QuestionScore.objects.update_or_create(
            answer=ans,
            defaults={
                'awarded_marks': awarded,
                'is_draft': False,
                'examiner_notes': 'Automated MCQ Scoring Engine evaluation.'
            }
        )

    return total_mcq_score


@transaction.atomic
def compute_attempt_totals(attempt: ExamAttempt) -> Dict[str, Any]:
    """
    Computes total aggregate marks awarded across all questions in an attempt.
    """
    answers = AttemptAnswer.objects.filter(attempt=attempt)
    total_awarded = Decimal('0.00')
    all_graded = True

    for ans in answers:
        if ans.marks_awarded is not None:
            total_awarded += ans.marks_awarded
        else:
            all_graded = False

    exam_total = Decimal(str(attempt.exam.total_marks))
    percentage = (total_awarded / exam_total * 100) if exam_total > 0 else Decimal('0.00')
    passing_pct = Decimal(str(attempt.exam.passing_percentage))
    is_passed = percentage >= passing_pct

    moderation, _ = GradeModeration.objects.get_or_create(
        attempt=attempt,
        defaults={
            'total_final_score': total_awarded,
            'is_passed': is_passed
        }
    )
    moderation.total_final_score = total_awarded
    moderation.is_passed = is_passed
    moderation.save(update_fields=['total_final_score', 'is_passed'])

    return {
        'total_score': total_awarded,
        'percentage': float(round(percentage, 2)),
        'is_passed': is_passed,
        'all_graded': all_graded
    }
