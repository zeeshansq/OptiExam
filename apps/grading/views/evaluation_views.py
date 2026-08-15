from decimal import Decimal
from django.views.generic import View, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from apps.core.mixins import GraderRequiredMixin
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import GraderAllocation, QuestionScore
from apps.grading.selectors.grader_selectors import get_batch_candidate_queue
from apps.grading.services.grading_service import save_question_evaluation
from apps.questions.models import QuestionRubric


class BatchCandidateQueueView(GraderRequiredMixin, DetailView):
    """
    Grader Double-Blind Queue View for an allocated candidate batch.
    """
    model = GraderAllocation
    template_name = 'grading/batch_queue.html'
    context_object_name = 'allocation'
    pk_url_kwarg = 'allocation_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['queue'] = get_batch_candidate_queue(self.object)
        return context


class GradingCockpitView(GraderRequiredMixin, View):
    """
    Split-Screen Double-Blind Evaluation Studio.
    """
    template_name = 'grading/grading_cockpit.html'

    def get(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(
            ExamAttempt.objects.select_related('exam', 'participant'),
            pk=attempt_id
        )

        subjective_answers = list(
            AttemptAnswer.objects.filter(
                attempt=attempt,
                question__question_type__in=['SHORT_ANSWER', 'LONG_ESSAY']
            ).select_related('question').order_by('order_in_attempt')
        )

        if not subjective_answers:
            messages.info(request, "No subjective questions requiring manual grading for this attempt.")
            return redirect('accounts:role_redirect')

        # Get first ungraded or draft answer
        current_answer = None
        for ans in subjective_answers:
            if not ans.is_graded:
                current_answer = ans
                break
        if not current_answer:
            current_answer = subjective_answers[0]

        grade_record = QuestionScore.objects.filter(answer=current_answer).first()
        rubrics = list(QuestionRubric.objects.filter(question=current_answer.question).order_by('order'))

        context = {
            'attempt': attempt,
            'current_answer': current_answer,
            'subjective_count': len(subjective_answers),
            'grade_record': grade_record,
            'rubrics': rubrics
        }
        return render(request, self.template_name, context)


class SaveEvaluationView(GraderRequiredMixin, View):
    """
    Saves or finalizes an evaluation score for a question.
    """
    def post(self, request, answer_id, *args, **kwargs):
        answer = get_object_or_404(AttemptAnswer.objects.select_related('attempt', 'question'), pk=answer_id)

        try:
            awarded = Decimal(request.POST.get('awarded_marks', '0.00'))
        except Exception:
            awarded = Decimal('0.00')

        is_draft = request.POST.get('is_draft') == 'True'
        notes = request.POST.get('examiner_notes', '')
        feedback = request.POST.get('feedback_to_student', '')
        client_version = int(request.POST.get('client_version', 1))

        # Extract rubric breakdown
        rubric_data = {}
        for key, val in request.POST.items():
            if key.startswith('rubric_'):
                rubric_id = key.replace('rubric_', '')
                try:
                    rubric_data[rubric_id] = float(val)
                except Exception:
                    pass

        try:
            save_question_evaluation(
                answer=answer,
                grader=request.user,
                awarded_marks=awarded,
                rubric_breakdown=rubric_data,
                examiner_notes=notes,
                feedback_to_student=feedback,
                is_draft=is_draft,
                client_version=client_version
            )
            messages.success(
                request,
                "Evaluation saved as draft." if is_draft else "Evaluation finalized and marked complete."
            )
        except Exception as e:
            messages.error(request, str(e))

        return redirect('grading:cockpit', attempt_id=answer.attempt.pk)
