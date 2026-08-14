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
    ExamRosterImportView
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

    # Participant Roster & 2-Stage Import
    path('exams/<int:exam_id>/roster/', ExamRosterHubView.as_view(), name='roster_hub'),
    path('exams/<int:exam_id>/roster/import/', ExamRosterImportView.as_view(), name='roster_import'),
]
