from django.urls import path
from apps.questions.views.bank_views import (
    QuestionBankListView,
    QuestionBankCreateView,
    QuestionBankUpdateView,
    QuestionBankDeleteView
)
from apps.questions.views.authoring_views import (
    QuestionListView,
    QuestionCreateMCQView,
    QuestionUpdateMCQView,
    QuestionCreateSubjectiveView,
    QuestionUpdateSubjectiveView,
    QuestionDetailView,
    QuestionDuplicateView,
    QuestionDeleteView
)
from apps.questions.views.import_views import QuestionBankImportView

app_name = 'questions'

urlpatterns = [
    # Question Banks
    path('banks/', QuestionBankListView.as_view(), name='bank_list'),
    path('banks/create/', QuestionBankCreateView.as_view(), name='bank_create'),
    path('banks/<int:bank_id>/', QuestionListView.as_view(), name='bank_detail'),
    path('banks/<int:bank_id>/edit/', QuestionBankUpdateView.as_view(), name='bank_update'),
    path('banks/<int:bank_id>/delete/', QuestionBankDeleteView.as_view(), name='bank_delete'),
    path('banks/<int:bank_id>/import/', QuestionBankImportView.as_view(), name='bank_import'),

    # Question Authoring Studio
    path('banks/<int:bank_id>/questions/create/mcq/', QuestionCreateMCQView.as_view(), name='question_create_mcq'),
    path('banks/<int:bank_id>/questions/create/subjective/', QuestionCreateSubjectiveView.as_view(), name='question_create_subjective'),
    path('questions/<int:question_id>/', QuestionDetailView.as_view(), name='question_detail'),
    path('questions/<int:question_id>/edit/mcq/', QuestionUpdateMCQView.as_view(), name='question_update_mcq'),
    path('questions/<int:question_id>/edit/subjective/', QuestionUpdateSubjectiveView.as_view(), name='question_update_subjective'),
    path('questions/<int:question_id>/duplicate/', QuestionDuplicateView.as_view(), name='question_duplicate'),
    path('questions/<int:question_id>/delete/', QuestionDeleteView.as_view(), name='question_delete'),
]
