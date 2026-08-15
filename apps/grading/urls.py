from django.urls import path
from apps.grading.views.allocation_views import (
    GraderAllocationListView,
    GraderAllocationCreateView
)
from apps.grading.views.evaluation_views import (
    BatchCandidateQueueView,
    GradingCockpitView,
    SaveEvaluationView
)
from apps.grading.views.moderation_views import (
    ModerationHubView,
    ModerationApproveView,
    ModerationReturnView
)

app_name = 'grading'

urlpatterns = [
    # Designer Allocation Matrix
    path('exams/<int:exam_id>/allocations/', GraderAllocationListView.as_view(), name='allocation_list'),
    path('exams/<int:exam_id>/allocations/create/', GraderAllocationCreateView.as_view(), name='allocation_create'),

    # Grader Double-Blind Queue & Cockpit
    path('batches/<int:allocation_id>/queue/', BatchCandidateQueueView.as_view(), name='batch_queue'),
    path('attempts/<int:attempt_id>/cockpit/', GradingCockpitView.as_view(), name='cockpit'),
    path('answers/<int:answer_id>/save-score/', SaveEvaluationView.as_view(), name='save_evaluation'),

    # Chief Examiner / Designer Grade Moderation Hub
    path('exams/<int:exam_id>/moderation/', ModerationHubView.as_view(), name='moderation_hub'),
    path('moderation/<int:moderation_id>/approve/', ModerationApproveView.as_view(), name='moderation_approve'),
    path('moderation/<int:moderation_id>/return/', ModerationReturnView.as_view(), name='moderation_return'),
]
