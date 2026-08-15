from django.urls import path
from apps.exams.views.blueprint_views import (
    ExamListView,
    ExamCreateView,
    ExamUpdateView,
    ExamDetailView,
    ExamDeleteView,
    ExamSectionBuilderView
)
from apps.exams.views.assignment_views import (
    QuestionPickerPaletteView,
    QuestionRemoveAssignmentView
)
from apps.exams.views.roster_views import (
    ExamRosterHubView,
    ExamRosterImportView,
    CandidateCreateView,
    CandidateDetailView,
    CandidateUpdateView,
    CandidateDeleteView
)
from apps.exams.views.live_ops_views import (
    LiveOpsView,
    LiveOpsBonusTimeAPIView
)

app_name = 'exams'

urlpatterns = [
    # Exam Blueprinting Hub
    path('exams/', ExamListView.as_view(), name='exam_list'),
    path('exams/create/', ExamCreateView.as_view(), name='exam_create'),
    path('exams/<int:exam_id>/', ExamDetailView.as_view(), name='exam_detail'),
    path('exams/<int:exam_id>/edit/', ExamUpdateView.as_view(), name='exam_update'),
    path('exams/<int:exam_id>/delete/', ExamDeleteView.as_view(), name='exam_delete'),
    
    # Section Management & Question Palette
    path('exams/<int:exam_id>/sections/', ExamSectionBuilderView.as_view(), name='section_builder'),
    path('sections/<int:section_id>/assign/', QuestionPickerPaletteView.as_view(), name='question_picker'),
    path('assignments/<int:assignment_id>/remove/', QuestionRemoveAssignmentView.as_view(), name='remove_assignment'),

    # Participant Roster CRUD & 2-Stage Import
    path('exams/<int:exam_id>/roster/', ExamRosterHubView.as_view(), name='roster_hub'),
    path('exams/<int:exam_id>/roster/add/', CandidateCreateView.as_view(), name='candidate_create'),
    path('exams/<int:exam_id>/roster/<int:entry_id>/', CandidateDetailView.as_view(), name='candidate_detail'),
    path('exams/<int:exam_id>/roster/<int:entry_id>/edit/', CandidateUpdateView.as_view(), name='candidate_update'),
    path('exams/<int:exam_id>/roster/<int:entry_id>/delete/', CandidateDeleteView.as_view(), name='candidate_delete'),
    path('exams/<int:exam_id>/roster/import/', ExamRosterImportView.as_view(), name='roster_import'),

    # Designer Live Ops Command Center
    path('exams/<int:exam_id>/live/', LiveOpsView.as_view(), name='live_ops'),
    path('exams/<int:exam_id>/live/bonus-time/', LiveOpsBonusTimeAPIView.as_view(), name='live_ops_bonus_time'),
]
