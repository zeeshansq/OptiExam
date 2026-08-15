from django.views.generic import DetailView
from django.shortcuts import get_object_or_404, render
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam
from apps.exams.services.analytics_service import compute_cohort_metrics, compute_item_analysis


class ExamAnalyticsDashboardView(DesignerRequiredMixin, DetailView):
    """
    Cohort Analytics Hub: Statistical histograms, pass rates, and section score comparisons.
    """
    model = Exam
    template_name = 'exams/exam_analytics.html'
    pk_url_kwarg = 'exam_id'
    context_object_name = 'exam'

    def get_queryset(self):
        return Exam.objects.for_tenant(self.request.tenant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cohort'] = compute_cohort_metrics(self.object)
        return context


class ExamItemAnalysisView(DesignerRequiredMixin, DetailView):
    """
    Pedagogical Item Analysis Hub: Difficulty Index (p-value) & Discrimination Index (r-value).
    """
    model = Exam
    template_name = 'exams/item_analysis.html'
    pk_url_kwarg = 'exam_id'
    context_object_name = 'exam'

    def get_queryset(self):
        return Exam.objects.for_tenant(self.request.tenant)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = compute_item_analysis(self.object)
        return context
