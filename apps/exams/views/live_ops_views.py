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
