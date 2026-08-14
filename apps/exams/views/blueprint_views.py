from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.db import transaction
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam, ExamSection, ExamLifelineConfig
from apps.exams.forms import ExamBlueprintForm, ExamFilterForm, ExamSectionFormSet, ExamLifelineConfigFormSet
from apps.exams.selectors.exam_selectors import get_tenant_exams

class ExamListView(DesignerRequiredMixin, ListView):
    model = Exam
    template_name = 'exams/exam_list.html'
    context_object_name = 'exams'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', self.paginate_by)
        try:
            val = int(page_size)
            if val in (10, 25, 50, 100):
                return val
        except (ValueError, TypeError):
            pass
        return self.paginate_by

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user.is_authenticated and self.request.user.is_super_admin():
            tenant = Tenant.objects.filter(is_active=True).first()
        if not tenant:
            return Exam.objects.none()

        q = self.request.GET.get('q', '').strip()
        subject = self.request.GET.get('subject', '').strip()
        status = self.request.GET.get('status', '').strip()
        sort_by = self.request.GET.get('sort', '-start_time')
        if self.request.GET.get('order') == 'asc' and not sort_by.startswith('-'):
            pass
        elif self.request.GET.get('order') == 'desc' and not sort_by.startswith('-'):
            sort_by = f"-{sort_by}"

        return get_tenant_exams(
            tenant=tenant,
            search_query=q,
            subject=subject,
            status_filter=status,
            sort_by=sort_by
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ExamFilterForm(self.request.GET)
        context['active_search_query'] = self.request.GET.get('q', '').strip()
        context['active_subject_filter'] = self.request.GET.get('subject', '').strip()
        context['active_status_filter'] = self.request.GET.get('status', '').strip()
        return context


class ExamCreateView(DesignerRequiredMixin, View):
    """
    Balanced 2-Column Multi-Section Exam Blueprint Creator.
    """
    template_name = 'exams/exam_form_wizard.html'

    def get(self, request, *args, **kwargs):
        form = ExamBlueprintForm()
        section_formset = ExamSectionFormSet(instance=Exam())
        return render(request, self.template_name, {
            'form': form,
            'section_formset': section_formset,
            'is_create': True
        })

    def post(self, request, *args, **kwargs):
        form = ExamBlueprintForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                exam = form.save(commit=False)
                tenant = getattr(request, 'tenant', None)
                if not tenant and request.user.is_super_admin():
                    tenant = Tenant.objects.filter(is_active=True).first()
                exam.tenant = tenant
                exam.created_by = request.user
                exam.save()

                section_formset = ExamSectionFormSet(request.POST, instance=exam)
                if section_formset.is_valid():
                    section_formset.save()
                else:
                    # Create default section if formset invalid/empty
                    ExamSection.objects.create(
                        exam=exam,
                        title="Section A — General",
                        order=1,
                        weightage=100.0
                    )

                # Initialize default lifelines
                for lt in ExamLifelineConfig.LifelineType.values:
                    ExamLifelineConfig.objects.get_or_create(
                        exam=exam,
                        lifeline_type=lt,
                        defaults={'is_enabled': True, 'max_allowed': 1}
                    )

                messages.success(request, f"Exam Blueprint '{exam.title}' ({exam.code}) created successfully.")
                return redirect('exams:exam_detail', exam_id=exam.pk)
        else:
            section_formset = ExamSectionFormSet(request.POST)

        return render(request, self.template_name, {
            'form': form,
            'section_formset': section_formset,
            'is_create': True
        })


class ExamUpdateView(DesignerRequiredMixin, View):
    template_name = 'exams/exam_form_wizard.html'

    def get_object(self):
        return get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['exam_id']
        )

    def get(self, request, exam_id, *args, **kwargs):
        exam = self.get_object()
        form = ExamBlueprintForm(instance=exam)
        section_formset = ExamSectionFormSet(instance=exam)
        lifeline_formset = ExamLifelineConfigFormSet(instance=exam)
        return render(request, self.template_name, {
            'exam': exam,
            'form': form,
            'section_formset': section_formset,
            'lifeline_formset': lifeline_formset,
            'is_create': False
        })

    def post(self, request, exam_id, *args, **kwargs):
        exam = self.get_object()
        form = ExamBlueprintForm(request.POST, instance=exam)
        section_formset = ExamSectionFormSet(request.POST, instance=exam)
        lifeline_formset = ExamLifelineConfigFormSet(request.POST, instance=exam)

        if form.is_valid() and section_formset.is_valid() and lifeline_formset.is_valid():
            with transaction.atomic():
                form.save()
                section_formset.save()
                lifeline_formset.save()
                messages.success(request, f"Exam Blueprint '{exam.title}' updated successfully.")
                return redirect('exams:exam_detail', exam_id=exam.pk)

        return render(request, self.template_name, {
            'exam': exam,
            'form': form,
            'section_formset': section_formset,
            'lifeline_formset': lifeline_formset,
            'is_create': False
        })


class ExamDetailView(DesignerRequiredMixin, DetailView):
    model = Exam
    template_name = 'exams/exam_detail.html'
    pk_url_kwarg = 'exam_id'
    context_object_name = 'exam'

    def get_queryset(self):
        return Exam.objects.for_tenant(self.request.tenant).prefetch_related(
            'sections',
            'sections__assignments',
            'sections__assignments__question',
            'lifeline_configs',
            'roster_entries'
        )


class ExamDeleteView(DesignerRequiredMixin, DeleteView):
    model = Exam
    template_name = 'exams/exam_confirm_delete.html'
    pk_url_kwarg = 'exam_id'
    success_url = reverse_lazy('exams:exam_list')

    def get_queryset(self):
        return Exam.objects.for_tenant(self.request.tenant)

    def form_valid(self, form):
        title = self.get_object().title
        messages.warning(self.request, f"Exam Blueprint '{title}' has been deleted.")
        return super().form_valid(form)


class ExamSectionBuilderView(DesignerRequiredMixin, View):
    """
    Dedicated Section Weightage Builder and Partition Manager.
    """
    template_name = 'exams/section_builder.html'

    def get_exam(self, exam_id):
        return get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=exam_id
        )

    def get(self, request, exam_id, *args, **kwargs):
        exam = self.get_exam(exam_id)
        formset = ExamSectionFormSet(instance=exam)
        return render(request, self.template_name, {'exam': exam, 'formset': formset})

    def post(self, request, exam_id, *args, **kwargs):
        exam = self.get_exam(exam_id)
        formset = ExamSectionFormSet(request.POST, instance=exam)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Exam sections updated successfully.")
            return redirect('exams:exam_detail', exam_id=exam.pk)

        return render(request, self.template_name, {'exam': exam, 'formset': formset})
