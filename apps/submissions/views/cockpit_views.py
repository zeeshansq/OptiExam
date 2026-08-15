from django.views.generic import View, TemplateView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from apps.exams.models import Exam
from apps.submissions.models import ExamAttempt
from apps.submissions.selectors.attempt_selectors import get_attempt_cockpit_state
from apps.submissions.services.attempt_service import initialize_attempt, reset_simulation_attempt
from apps.submissions.services.submission_service import finalize_submission


class ExamCockpitView(LoginRequiredMixin, View):
    """
    100% Fullscreen Live Examination Cockpit.
    """
    template_name = 'submissions/exam_cockpit.html'

    def get(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(
            ExamAttempt.objects.select_related('exam', 'participant'),
            pk=attempt_id
        )

        # Ensure user owns attempt or is super admin
        if attempt.participant != request.user and not request.user.is_super_admin():
            raise PermissionDenied("You do not have authorization to view this examination cockpit.")

        if attempt.status != ExamAttempt.Status.IN_PROGRESS:
            return render(request, 'submissions/submission_receipt.html', {'attempt': attempt})

        if attempt.is_expired:
            if attempt.is_simulation:
                # Reset simulation automatically
                reset_simulation_attempt(attempt.exam, request.user)
                return redirect('submissions:dry_run_simulation', exam_id=attempt.exam.pk)
            else:
                finalize_submission(attempt)
                return render(request, 'submissions/submission_receipt.html', {'attempt': attempt})

        state = get_attempt_cockpit_state(attempt)
        return render(request, self.template_name, state)



class ExamSubmitView(LoginRequiredMixin, View):
    """
    Finalizes submission of an active exam attempt.
    Supports both POST (manual button) and GET (auto-submit timeout / violation redirects).
    """
    def _finalize_and_render(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt, pk=attempt_id)
        if attempt.participant != request.user and not request.user.is_super_admin():
            raise PermissionDenied()

        finalize_submission(attempt)
        return render(request, 'submissions/submission_receipt.html', {'attempt': attempt})

    def post(self, request, attempt_id, *args, **kwargs):
        return self._finalize_and_render(request, attempt_id)

    def get(self, request, attempt_id, *args, **kwargs):
        return self._finalize_and_render(request, attempt_id)



class CandidateDryRunSimulationView(LoginRequiredMixin, View):
    """
    Candidate Dry-Run Simulation Studio:
    Allows Designers (Tenant Admins) & authorized Item Writers to test the exact candidate experience.
    """
    def get(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            Exam.objects.for_tenant(request.tenant),
            pk=exam_id
        )

        # Authorization: Designers or Item Writers
        if not (request.user.is_designer() or request.user.is_item_writer() or request.user.is_super_admin()):
            raise PermissionDenied("Dry-Run Simulation is reserved for Designers and Item Writers.")

        attempt = initialize_attempt(
            exam=exam,
            participant=request.user,
            is_simulation=True
        )

        state = get_attempt_cockpit_state(attempt)
        state['is_simulation'] = True
        return render(request, 'submissions/exam_cockpit.html', state)


class SimulationResetView(LoginRequiredMixin, View):
    """
    Resets simulation session and generates a fresh randomized seed.
    """
    def get(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            Exam.objects.for_tenant(request.tenant),
            pk=exam_id
        )

        reset_simulation_attempt(exam, request.user)
        messages.success(request, "Dry-run simulation reset. Question order re-seeded.")
        return redirect('submissions:dry_run_simulation', exam_id=exam.pk)
