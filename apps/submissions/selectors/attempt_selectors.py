from typing import Optional, List, Dict, Any
from django.db.models import Prefetch
from apps.exams.models import Exam, ExamSection, ExamLifelineConfig
from apps.submissions.models import ExamAttempt, AttemptAnswer, AttemptLifelineUsage
from apps.questions.models import Question, QuestionOption


def get_candidate_active_attempt(exam: Exam, user, is_simulation: bool = False) -> Optional[ExamAttempt]:
    """
    Retrieves the candidate's attempt for an exam.
    """
    return ExamAttempt.objects.filter(
        exam=exam,
        participant=user,
        is_simulation=is_simulation
    ).first()


def get_attempt_cockpit_state(attempt: ExamAttempt) -> Dict[str, Any]:
    """
    Assembles the complete state payload for rendering the Live Examination Cockpit.
    """
    exam = attempt.exam
    answers = list(
        AttemptAnswer.objects.filter(attempt=attempt)
        .select_related('question')
        .prefetch_related('selected_options', 'question__options')
        .order_by('order_in_attempt')
    )

    lifeline_configs = list(ExamLifelineConfig.objects.filter(exam=exam, is_enabled=True))
    lifeline_usages = list(AttemptLifelineUsage.objects.filter(attempt=attempt))

    # Calculate remaining usages per lifeline
    lifelines_state = {}
    for cfg in lifeline_configs:
        used_count = sum(1 for u in lifeline_usages if u.lifeline_type == cfg.lifeline_type)
        lifelines_state[cfg.lifeline_type] = {
            'code': cfg.lifeline_type,
            'name': cfg.get_lifeline_type_display(),
            'max_allowed': cfg.max_allowed,
            'used_count': used_count,
            'remaining': max(0, cfg.max_allowed - used_count),
            'is_available': (cfg.max_allowed - used_count) > 0
        }

    # Format question list with options & answer state
    questions_data = []
    for ans in answers:
        q = ans.question
        options_list = list(q.options.all())
        
        # If exam shuffles options, randomize deterministically with candidate_seed + question.id
        if exam.shuffle_options:
            import random
            opt_rng = random.Random(attempt.candidate_seed + q.id)
            opt_rng.shuffle(options_list)

        selected_opt_ids = [opt.id for opt in ans.selected_options.all()]

        questions_data.append({
            'order': ans.order_in_attempt,
            'question_id': q.id,
            'question_type': q.question_type,
            'prompt': q.prompt,
            'points': float(q.points),
            'difficulty': q.difficulty,
            'blooms_level': q.blooms_level,
            'image_url': q.image_asset.url if q.image_asset else None,
            'word_limit': getattr(q, 'word_limit', None),
            'options': [
                {'id': opt.id, 'text': opt.option_text, 'order': opt.order}
                for opt in options_list
            ],
            'answer': {
                'selected_option_ids': selected_opt_ids,
                'text_response': ans.text_response,
                'is_bookmarked': ans.is_bookmarked,
                'is_skipped': ans.is_skipped,
                'is_answered': len(selected_opt_ids) > 0 or bool(ans.text_response.strip())
            }
        })

    import json

    # Determine current active question index based on candidate's saved pointer
    active_q_index = 0
    if attempt.current_question_id:
        for idx, q_item in enumerate(questions_data):
            if q_item['question_id'] == attempt.current_question_id:
                active_q_index = idx
                break

    return {
        'attempt': attempt,
        'exam': exam,
        'remaining_seconds': attempt.remaining_seconds,
        'total_allowed_seconds': attempt.total_allowed_seconds,
        'questions_count': len(questions_data),
        'questions': questions_data,
        'questions_json': json.dumps(questions_data),
        'active_question_index': active_q_index,
        'lifelines': lifelines_state,
        'enforce_fullscreen': exam.enforce_fullscreen,
        'lock_copy_paste': exam.lock_copy_paste,
        'allow_back_navigation': exam.allow_back_navigation,
        'is_simulation': attempt.is_simulation
    }


