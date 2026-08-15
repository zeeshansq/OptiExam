import random
from typing import Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.exams.models import ExamLifelineConfig, ExamQuestionAssignment
from apps.submissions.models import ExamAttempt, AttemptAnswer, AttemptLifelineUsage, ProctoringLog
from apps.questions.models import Question, QuestionOption


@transaction.atomic
def execute_lifeline(
    attempt: ExamAttempt,
    lifeline_type: str,
    question_id: int
) -> Dict[str, Any]:

    """
    Executes an active lifeline requested by candidate during examination.
    """
    # Check if lifeline is enabled for this exam
    config = ExamLifelineConfig.objects.filter(
        exam=attempt.exam,
        lifeline_type=lifeline_type,
        is_enabled=True
    ).first()

    if not config:
        return {'success': False, 'error': f"Lifeline '{lifeline_type}' is not enabled for this exam."}

    # Check usage quota limit
    usages_count = AttemptLifelineUsage.objects.filter(
        attempt=attempt,
        lifeline_type=lifeline_type
    ).count()

    if usages_count >= config.max_allowed:
        return {
            'success': False,
            'error': f"Lifeline quota exhausted (Maximum {config.max_allowed} uses allowed)."
        }

    question = Question.objects.filter(pk=question_id).first()
    if not question:
        return {'success': False, 'error': "Invalid question reference."}

    details = {}

    if lifeline_type == ExamLifelineConfig.LifelineType.FIFTY_FIFTY:
        if question.question_type not in (Question.QuestionType.MCQ_SINGLE, Question.QuestionType.MCQ_MULTIPLE, Question.QuestionType.IMAGE_MCQ):
            return {'success': False, 'error': "50:50 Eliminator is only applicable to multiple-choice questions."}

        options = list(question.options.all())
        incorrect_options = [opt for opt in options if not opt.is_correct]

        if len(incorrect_options) < 2:
            return {'success': False, 'error': "Not enough incorrect options to eliminate."}

        eliminated = random.sample(incorrect_options, 2)
        eliminated_ids = [opt.id for opt in eliminated]
        details['eliminated_option_ids'] = eliminated_ids

    elif lifeline_type == ExamLifelineConfig.LifelineType.HINT_TOKEN:
        if not question.hint_text:
            return {'success': False, 'error': "No guidance hint available for this question."}
        details['hint_text'] = question.hint_text

    elif lifeline_type == ExamLifelineConfig.LifelineType.BOOKMARK_FLAG:
        ans = AttemptAnswer.objects.filter(attempt=attempt, question=question).first()
        if ans:
            ans.is_bookmarked = not ans.is_bookmarked
            ans.save(update_fields=['is_bookmarked'])
            details['is_bookmarked'] = ans.is_bookmarked


    # Log usage
    usage = AttemptLifelineUsage.objects.create(
        attempt=attempt,
        lifeline_type=lifeline_type,
        question=question,
        details=details
    )

    ProctoringLog.objects.create(
        attempt=attempt,
        event_type=ProctoringLog.EventType.LIFELINE_USED,
        details={'lifeline_type': lifeline_type, 'question_id': question_id}
    )

    return {
        'success': True,
        'lifeline_type': lifeline_type,
        'remaining_quota': config.max_allowed - (usages_count + 1),
        'data': details
    }
