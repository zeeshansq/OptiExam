import json
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.submissions.models import ExamAttempt
from apps.submissions.services.heartbeat_service import process_heartbeat
from apps.submissions.services.lifeline_service import execute_lifeline
from apps.submissions.services.proctoring_service import log_proctoring_event


class HeartbeatAPIView(LoginRequiredMixin, View):
    """
    15-second heartbeat API endpoint for answer delta auto-save and clock synchronization.
    """
    def post(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(ExamAttempt, pk=attempt_id)
        if attempt.participant != request.user and not request.user.is_super_admin():
            return JsonResponse({'status': 'unauthorized'}, status=403)

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        active_q_id = body.get('active_question_id')
        delta = body.get('answers_delta', [])

        result = process_heartbeat(
            attempt=attempt,
            active_question_id=active_q_id,
            answers_delta=delta
        )
        return JsonResponse(result)


class LifelineExecuteAPIView(LoginRequiredMixin, View):
    """
    Executes a lifeline (50:50, hint, skip, bookmark).
    """
    def post(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(ExamAttempt, pk=attempt_id)
        if attempt.participant != request.user and not request.user.is_super_admin():
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        lifeline_type = body.get('lifeline_type')
        question_id = body.get('question_id')

        result = execute_lifeline(attempt, lifeline_type, question_id)
        return JsonResponse(result)


class ProctoringViolationAPIView(LoginRequiredMixin, View):
    """
    Logs client-detected proctoring violation.
    """
    def post(self, request, attempt_id, *args, **kwargs):
        attempt = get_object_or_404(ExamAttempt, pk=attempt_id)
        if attempt.participant != request.user and not request.user.is_super_admin():
            return JsonResponse({'status': 'unauthorized'}, status=403)

        try:
            body = json.loads(request.body.decode('utf-8'))
        except Exception:
            body = {}

        event_type = body.get('event_type')
        details = body.get('details', {})

        log_proctoring_event(attempt, event_type, details)
        return JsonResponse({
            'status': 'logged',
            'violations': attempt.violation_count,
            'is_auto_submitted': attempt.status == ExamAttempt.Status.AUTO_SUBMITTED,
            'max_violations': attempt.exam.max_tab_switch_limit
        })

