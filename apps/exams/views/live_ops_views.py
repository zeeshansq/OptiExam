import json
from django.views.generic import DetailView, View
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.utils import timezone
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam
from apps.submissions.models import ExamAttempt


class LiveOpsView(DesignerRequiredMixin, DetailView):
    """
    Designer Real-Time Live Examination Command Center.
    Monitors candidate attempts, heartbeats, violations, and provides dynamic bonus time controls.
    """
    model = Exam
    template_name = 'exams/live_ops.html'
    pk_url_kwarg = 'exam_id'
    context_object_name = 'exam'

    def get_queryset(self):
        return Exam.objects.for_tenant(self.request.tenant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = ExamAttempt.objects.filter(
            exam=self.object,
            is_simulation=False
        ).select_related('participant', 'participant__profile')
        context['attempts'] = attempts
        return context


class LiveOpsBonusTimeAPIView(DesignerRequiredMixin, View):
    """
    Dynamically injects bonus minutes to an active attempt or all exam attempts on-the-fly.
    """
    def post(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(Exam.objects.for_tenant(request.tenant), pk=exam_id)

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        attempt_id = body.get('attempt_id')
        bonus_mins = int(body.get('bonus_minutes', 5))

        if attempt_id:
            attempt = get_object_or_404(ExamAttempt, exam=exam, pk=attempt_id)
            attempt.bonus_minutes_awarded += bonus_mins
            attempt.save(update_fields=['bonus_minutes_awarded'])
            return JsonResponse({'status': 'success', 'awarded_to': 'single', 'new_bonus': attempt.bonus_minutes_awarded})
        else:
            attempts = ExamAttempt.objects.filter(exam=exam, status=ExamAttempt.Status.IN_PROGRESS)
            count = 0
            for att in attempts:
                att.bonus_minutes_awarded += bonus_mins
                att.save(update_fields=['bonus_minutes_awarded'])
                count += 1
            return JsonResponse({'status': 'success', 'awarded_to': 'all', 'affected_count': count})


class LiveOpsUnlockAttemptAPIView(DesignerRequiredMixin, View):
    """
    Allows examiners and designers to unlock/resume an attempt that was auto-submitted or locked
    due to proctoring violation limit or accidental exit.
    """
    def post(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(Exam.objects.for_tenant(request.tenant), pk=exam_id)


        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        attempt_id = body.get('attempt_id')
        reset_violations = bool(body.get('reset_violations', True))
        bonus_mins = int(body.get('bonus_minutes', 0))

        attempt = get_object_or_404(ExamAttempt, exam=exam, pk=attempt_id)
        attempt.status = ExamAttempt.Status.IN_PROGRESS
        attempt.submitted_at = None
        
        if reset_violations:
            attempt.violation_count = 0

        if bonus_mins > 0:
            attempt.bonus_minutes_awarded += bonus_mins

        attempt.save(update_fields=['status', 'submitted_at', 'violation_count', 'bonus_minutes_awarded'])

        # Log designer override in ProctoringLog stream
        from apps.submissions.models import ProctoringLog
        ProctoringLog.objects.create(
            attempt=attempt,
            event_type=ProctoringLog.EventType.VIOLATION_RECORDED,
            details={
                'action': 'PROCTOR_UNLOCK_OVERRIDE',
                'unlocked_by': request.user.username,
                'reset_violations': reset_violations,
                'bonus_minutes_awarded': bonus_mins,
                'timestamp': timezone.now().isoformat()
            }
        )

        return JsonResponse({
            'status': 'success',
            'message': f"Candidate {attempt.participant.username}'s attempt has been unlocked and resumed.",
            'attempt_status': attempt.status,
            'violation_count': attempt.violation_count,
            'bonus_minutes': attempt.bonus_minutes_awarded
        })

