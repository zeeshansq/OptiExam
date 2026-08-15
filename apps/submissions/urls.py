from django.urls import path
from apps.submissions.views.lobby_views import (
    ExamLobbyView,
    ExamStartView
)
from apps.submissions.views.cockpit_views import (
    ExamCockpitView,
    ExamSubmitView,
    CandidateDryRunSimulationView,
    SimulationResetView
)
from apps.submissions.views.api_views import (
    HeartbeatAPIView,
    LifelineExecuteAPIView,
    ProctoringViolationAPIView
)

app_name = 'submissions'

urlpatterns = [
    # Candidate Lobby & Entry
    path('exams/<int:exam_id>/lobby/', ExamLobbyView.as_view(), name='exam_lobby'),
    path('exams/<int:exam_id>/start/', ExamStartView.as_view(), name='exam_start'),

    # Fullscreen Live Examination Cockpit
    path('attempts/<int:attempt_id>/cockpit/', ExamCockpitView.as_view(), name='exam_cockpit'),
    path('attempts/<int:attempt_id>/submit/', ExamSubmitView.as_view(), name='exam_submit'),

    # Candidate Dry-Run Simulation Studio (Designer & Item Writer)
    path('exams/<int:exam_id>/dry-run/', CandidateDryRunSimulationView.as_view(), name='dry_run_simulation'),
    path('exams/<int:exam_id>/dry-run/reset/', SimulationResetView.as_view(), name='simulation_reset'),

    # Async Heartbeat & Telemetry APIs
    path('api/attempts/<int:attempt_id>/heartbeat/', HeartbeatAPIView.as_view(), name='api_heartbeat'),
    path('api/attempts/<int:attempt_id>/lifelines/execute/', LifelineExecuteAPIView.as_view(), name='api_lifeline'),
    path('api/attempts/<int:attempt_id>/proctoring/violation/', ProctoringViolationAPIView.as_view(), name='api_violation'),
]
