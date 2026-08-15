from django.views.generic import ListView, CreateView, DetailView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam
from apps.grading.models import GraderAllocation
from apps.grading.forms import GraderAllocationForm
from apps.grading.services.allocation_service import create_grader_allocation


class GraderAllocationListView(DesignerRequiredMixin, ListView):
    """
    Designer Batch Allocation Matrix: View and partition candidate ranges across examiners.
    """
    model = GraderAllocation
    template_name = 'grading/allocation_list.html'
    context_object_name = 'allocations'

    def get_queryset(self):
        self.exam = get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['exam_id']
        )
        return GraderAllocation.objects.filter(exam=self.exam).select_related('grader', 'section_scope')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = self.exam
        return context


class GraderAllocationCreateView(DesignerRequiredMixin, CreateView):
    """
    Allocates a candidate index batch to an evaluation officer.
    """
    model = GraderAllocation
    form_class = GraderAllocationForm
    template_name = 'grading/allocation_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.exam = get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['exam_id']
        )
        kwargs['exam'] = self.exam
        return kwargs

    def form_valid(self, form):
        try:
            create_grader_allocation(
                exam=self.exam,
                grader=form.cleaned_data['grader'],
                candidate_range_start=form.cleaned_data['candidate_range_start'],
                candidate_range_end=form.cleaned_data['candidate_range_end'],
                sla_deadline=form.cleaned_data.get('sla_deadline'),
                section_scope=form.cleaned_data.get('section_scope')
            )
            messages.success(self.request, f"Batch allocation created for {form.cleaned_data['grader'].username}.")
            return redirect('grading:allocation_list', exam_id=self.exam.pk)
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = self.exam
        return context
