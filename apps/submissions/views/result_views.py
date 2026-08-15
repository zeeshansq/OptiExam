from django.views.generic import View, DetailView
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from apps.exams.models import Exam
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import QuestionScore, GradeModeration


class ExamResultView(LoginRequiredMixin, View):
    """
    Participant Official Scorecard & Transcript View with print support.
    """
    template_name = 'submissions/exam_result.html'

    def get(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            Exam.objects.for_tenant(request.tenant),
            pk=exam_id
        )

        # Access Guard: results must be published
        if not exam.results_published and not (request.user.is_designer() or request.user.is_super_admin()):
            return render(request, 'submissions/result_pending.html', {'exam': exam})

        attempt = ExamAttempt.objects.filter(
            exam=exam,
            participant=request.user,
            is_simulation=False
        ).select_related('grade_moderation').first()

        if not attempt:
            raise PermissionDenied("No examination attempt found for your account.")

        answers = list(
            AttemptAnswer.objects.filter(attempt=attempt)
            .select_related('question')
            .prefetch_related('selected_options', 'question__options')
            .order_by('order_in_attempt')
        )

        # Collect question-level score breakdown
        question_breakdown = []
        for ans in answers:
            score_record = QuestionScore.objects.filter(answer=ans).first()
            question_breakdown.append({
                'answer': ans,
                'question': ans.question,
                'score_record': score_record,
                'correct_options': ans.question.options.filter(is_correct=True) if ans.question.is_mcq else None
            })

        moderation = getattr(attempt, 'grade_moderation', None)

        context = {
            'exam': exam,
            'attempt': attempt,
            'moderation': moderation,
            'question_breakdown': question_breakdown,
            'show_feedback': exam.show_grader_feedback
        }
        return render(request, self.template_name, context)
