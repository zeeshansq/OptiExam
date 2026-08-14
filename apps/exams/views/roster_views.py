from django.views.generic import ListView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam, ExamParticipantRoster
from apps.exams.forms import RosterCSVImportForm, RosterFilterForm
from apps.exams.selectors.exam_selectors import get_exam_roster
from apps.exams.services.roster_service import (
    parse_and_validate_roster_rows,
    commit_roster_import
)

class ExamRosterHubView(DesignerRequiredMixin, ListView):
    """
    Official Candidate Roster Directory with sequential candidate_index for double-blind human grading.
    """
    model = ExamParticipantRoster
    template_name = 'exams/roster_hub.html'
    context_object_name = 'roster_entries'
    paginate_by = 25

    def get_exam(self):
        return get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['exam_id']
        )

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
        exam = self.get_exam()
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        return get_exam_roster(exam=exam, search_query=q, status=status)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = self.get_exam()
        context['filter_form'] = RosterFilterForm(self.request.GET)
        context['active_search_query'] = self.request.GET.get('q', '').strip()
        context['active_status_filter'] = self.request.GET.get('status', '').strip()
        return context


class ExamRosterImportView(DesignerRequiredMixin, View):
    """
    Two-Stage Candidate Roster Import Hub:
    Stage 1: Dry-run schema validation (0 DB writes) -> 10-row preview & error audit.
    Stage 2: Atomic commit generating accounts and sequential candidate_index (1..N).
    """
    template_name = 'exams/roster_import.html'

    def get_exam(self, exam_id):
        return get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=exam_id
        )

    def get(self, request, exam_id, *args, **kwargs):
        exam = self.get_exam(exam_id)
        form = RosterCSVImportForm()
        return render(request, self.template_name, {
            'exam': exam,
            'form': form,
            'stage': 'upload'
        })

    def post(self, request, exam_id, *args, **kwargs):
        exam = self.get_exam(exam_id)
        action = request.POST.get('action', 'validate')

        if action == 'validate':
            form = RosterCSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES['file']
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name

                validation_result = parse_and_validate_roster_rows(file_bytes, filename)
                
                if validation_result['valid_rows']:
                    request.session['staged_roster_rows'] = validation_result['valid_rows']
                    request.session['staged_roster_filename'] = filename
                else:
                    request.session.pop('staged_roster_rows', None)

                return render(request, self.template_name, {
                    'exam': exam,
                    'form': form,
                    'stage': 'preview',
                    'result': validation_result,
                    'filename': filename
                })

        elif action == 'commit':
            staged_rows = request.session.get('staged_roster_rows', [])
            filename = request.session.get('staged_roster_filename', 'roster.csv')
            if not staged_rows:
                messages.error(request, "No staged candidate roster found to commit. Please re-upload.")
                return redirect('exams:roster_import', exam_id=exam.pk)

            job = commit_roster_import(
                exam=exam,
                valid_rows=staged_rows,
                user=request.user,
                source_filename=filename
            )

            request.session.pop('staged_roster_rows', None)
            request.session.pop('staged_roster_filename', None)

            messages.success(request, f"Successfully enrolled {job.successful_rows} candidates into '{exam.title}'.")
            return redirect('exams:roster_hub', exam_id=exam.pk)

        return redirect('exams:roster_import', exam_id=exam.pk)
