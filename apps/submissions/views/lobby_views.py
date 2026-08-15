from django.views.generic import DetailView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from apps.exams.models import Exam
from apps.submissions.models import ExamAttempt
from apps.submissions.services.attempt_service import initialize_attempt
from apps.submissions.selectors.attempt_selectors import get_candidate_active_attempt


class ExamLobbyView(LoginRequiredMixin, DetailView):
    """
    Participant Pre-Exam Lobby with instructions, schedule window, and launch trigger.
    """
    model = Exam
    template_name = 'submissions/exam_lobby.html'
    pk_url_kwarg = 'exam_id'
    context_object_name = 'exam'

    def get_queryset(self):
        return Exam.objects.for_tenant(self.request.tenant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        existing_attempt = get_candidate_active_attempt(self.object, self.request.user)
        context['existing_attempt'] = existing_attempt
        return context


class ExamStartView(LoginRequiredMixin, View):
    """
    Initializes/resumes the candidate exam session and redirects to the Live Examination Cockpit.
    """
    def post(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            Exam.objects.for_tenant(request.tenant),
            pk=exam_id
        )

        try:
            attempt = initialize_attempt(
                exam=exam,
                participant=request.user,
                client_ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            return redirect('submissions:exam_cockpit', attempt_id=attempt.pk)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('submissions:exam_lobby', exam_id=exam.pk)
