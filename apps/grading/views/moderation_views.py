from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import GradeModeration, QuestionScore
from apps.grading.services.moderation_service import approve_grade_moderation, return_grade_for_reevaluation


class ModerationHubView(DesignerRequiredMixin, ListView):
    """
    Chief Examiner / Designer Grade Moderation & Sign-Off Hub.
    """
    model = GradeModeration
    template_name = 'grading/moderation_hub.html'
    context_object_name = 'moderation_records'

    def get_queryset(self):
        self.exam = get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['exam_id']
        )
        return GradeModeration.objects.filter(
            attempt__exam=self.exam,
            attempt__is_simulation=False
        ).select_related('attempt', 'attempt__participant', 'moderator')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = self.exam
        return context


class ModerationApproveView(DesignerRequiredMixin, View):
    """
    Approves candidate evaluation score.
    """
    def post(self, request, moderation_id, *args, **kwargs):
        moderation = get_object_or_404(
            GradeModeration.objects.select_related('attempt', 'attempt__exam'),
            pk=moderation_id
        )
        notes = request.POST.get('moderation_notes', '')
        approve_grade_moderation(moderation, request.user, notes)
        messages.success(request, f"Score for Attempt #{moderation.attempt.id} approved and signed off.")
        return redirect('grading:moderation_hub', exam_id=moderation.attempt.exam.pk)


class ModerationReturnView(DesignerRequiredMixin, View):
    """
    Returns candidate evaluation score for re-evaluation by examiner.
    """
    def post(self, request, moderation_id, *args, **kwargs):
        moderation = get_object_or_404(
            GradeModeration.objects.select_related('attempt', 'attempt__exam'),
            pk=moderation_id
        )
        revision_notes = request.POST.get('revision_notes', '')
        try:
            return_grade_for_reevaluation(moderation, request.user, revision_notes)
            messages.warning(request, f"Attempt #{moderation.attempt.id} returned to examiner with revision directions.")
        except Exception as e:
            messages.error(request, str(e))

        return redirect('grading:moderation_hub', exam_id=moderation.attempt.exam.pk)
