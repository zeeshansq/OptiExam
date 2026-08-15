from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.exams.models import Exam, ExamParticipantRoster
from apps.submissions.models import ExamAttempt


class ParticipantHistoryView(LoginRequiredMixin, ListView):
    """
    Participant 'My Exams' History & Transcript Portal.
    """
    template_name = 'submissions/participant_history.html'
    context_object_name = 'exam_history'

    def get_queryset(self):
        user = self.request.user
        rosters = ExamParticipantRoster.objects.filter(
            participant=user
        ).select_related('exam')

        history = []
        for r in rosters:
            ex = r.exam
            att = ExamAttempt.objects.filter(
                exam=ex,
                participant=user,
                is_simulation=False
            ).select_related('grade_moderation').first()

            history.append({
                'exam': ex,
                'attempt': att,
                'roster': r
            })

        return history
