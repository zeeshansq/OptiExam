from django.views.generic import DetailView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam
from apps.exams.services.publication_service import publish_exam_results


class ExamPublishResultsView(DesignerRequiredMixin, View):
    """
    Toggles official result publication for an examination blueprint.
    """
    def post(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            Exam.objects.for_tenant(request.tenant),
            pk=exam_id
        )

        show_feedback = request.POST.get('show_grader_feedback') == 'on'

        if not exam.results_published:
            publish_exam_results(exam, show_feedback, request.user)
            messages.success(request, f"Official results for '{exam.title}' have been published to candidate scorecards.")
        else:
            # Unpublish
            exam.results_published = False
            exam.save(update_fields=['results_published'])
            messages.warning(request, f"Results publication for '{exam.title}' has been revoked.")

        return redirect('exams:exam_detail', exam_id=exam.pk)
