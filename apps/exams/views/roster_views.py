from django.views.generic import ListView, View, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.core.mixins import DesignerRequiredMixin
from apps.accounts.models import UserRole, UserProfile
from apps.exams.models import Exam, ExamParticipantRoster
from apps.exams.forms import (
    RosterCSVImportForm,
    RosterFilterForm,
    CandidateEnrollmentForm,
    CandidateEditForm
)
from apps.exams.selectors.exam_selectors import get_exam_roster
from apps.exams.services.roster_service import (
    parse_and_validate_roster_rows,
    commit_roster_import
)

User = get_user_model()


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


class CandidateCreateView(DesignerRequiredMixin, View):
    """
    Manually enroll a single candidate into an Exam Roster.
    """
    template_name = 'exams/candidate_form.html'

    def get_exam(self, exam_id):
        return get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=exam_id
        )

    def get(self, request, exam_id, *args, **kwargs):
        exam = self.get_exam(exam_id)
        form = CandidateEnrollmentForm()
        return render(request, self.template_name, {
            'exam': exam,
            'form': form,
            'is_create': True
        })

    def post(self, request, exam_id, *args, **kwargs):
        exam = self.get_exam(exam_id)
        form = CandidateEnrollmentForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            first_name = form.cleaned_data['first_name'].strip()
            last_name = form.cleaned_data['last_name'].strip()
            reg_num = form.cleaned_data['registration_number'].strip()
            department = form.cleaned_data.get('department', '').strip()
            batch_year = form.cleaned_data.get('batch_year', '').strip()
            status = form.cleaned_data['status']

            with transaction.atomic():
                # Check if registration number already enrolled in this exam
                if ExamParticipantRoster.objects.filter(exam=exam, registration_number=reg_num).exists():
                    form.add_error('registration_number', f"Registration number '{reg_num}' is already enrolled in this exam.")
                    return render(request, self.template_name, {'exam': exam, 'form': form, 'is_create': True})

                clean_username = reg_num.lower().replace(' ', '_').replace('-', '_')
                student_user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': clean_username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'tenant': exam.tenant,
                        'role': UserRole.PARTICIPANT,
                        'is_active': True
                    }
                )

                if created:
                    student_user.set_unusable_password()
                    student_user.save()
                else:
                    student_user.first_name = first_name
                    student_user.last_name = last_name
                    student_user.save()

                UserProfile.objects.update_or_create(
                    user=student_user,
                    defaults={
                        'registration_number': reg_num,
                        'department': department,
                        'batch_year': batch_year
                    }
                )

                if ExamParticipantRoster.objects.filter(exam=exam, participant=student_user).exists():
                    form.add_error('email', f"Candidate '{email}' is already enrolled in this exam.")
                    return render(request, self.template_name, {'exam': exam, 'form': form, 'is_create': True})

                current_max = ExamParticipantRoster.objects.filter(exam=exam).count() + 1
                roster_entry = ExamParticipantRoster.objects.create(
                    exam=exam,
                    participant=student_user,
                    candidate_index=current_max,
                    registration_number=reg_num,
                    status=status
                )

                messages.success(request, f"Candidate #{roster_entry.candidate_index:03d} ({first_name} {last_name}) enrolled successfully.")
                return redirect('exams:roster_hub', exam_id=exam.pk)

        return render(request, self.template_name, {'exam': exam, 'form': form, 'is_create': True})


class CandidateDetailView(DesignerRequiredMixin, DetailView):
    """
    Inspect a candidate's enrollment profile, blind grading index, and exam status.
    """
    model = ExamParticipantRoster
    template_name = 'exams/candidate_detail.html'
    context_object_name = 'entry'
    pk_url_kwarg = 'entry_id'

    def get_queryset(self):
        exam = get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['exam_id']
        )
        return ExamParticipantRoster.objects.filter(exam=exam).select_related('participant', 'participant__profile', 'exam')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exam'] = self.object.exam
        return context


class CandidateUpdateView(DesignerRequiredMixin, View):
    """
    Update a candidate's registration number, status, or profile details.
    """
    template_name = 'exams/candidate_form.html'

    def get_entry(self, exam_id, entry_id):
        exam = get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=exam_id
        )
        return get_object_or_404(
            ExamParticipantRoster.objects.filter(exam=exam).select_related('participant', 'participant__profile'),
            pk=entry_id
        )

    def get(self, request, exam_id, entry_id, *args, **kwargs):
        entry = self.get_entry(exam_id, entry_id)
        form = CandidateEditForm(instance=entry)
        return render(request, self.template_name, {
            'exam': entry.exam,
            'entry': entry,
            'form': form,
            'is_create': False
        })

    def post(self, request, exam_id, entry_id, *args, **kwargs):
        entry = self.get_entry(exam_id, entry_id)
        form = CandidateEditForm(request.POST, instance=entry)
        if form.is_valid():
            with transaction.atomic():
                entry = form.save()
                participant = entry.participant
                participant.first_name = form.cleaned_data['first_name'].strip()
                participant.last_name = form.cleaned_data['last_name'].strip()
                participant.email = form.cleaned_data['email'].lower().strip()
                participant.save()

                UserProfile.objects.update_or_create(
                    user=participant,
                    defaults={
                        'registration_number': entry.registration_number,
                        'department': form.cleaned_data.get('department', '').strip(),
                        'batch_year': form.cleaned_data.get('batch_year', '').strip()
                    }
                )

                messages.success(request, f"Candidate #{entry.candidate_index:03d} updated successfully.")
                return redirect('exams:roster_hub', exam_id=entry.exam.pk)

        return render(request, self.template_name, {
            'exam': entry.exam,
            'entry': entry,
            'form': form,
            'is_create': False
        })


class CandidateDeleteView(DesignerRequiredMixin, View):
    """
    Remove or revoke a candidate from an exam roster.
    """
    template_name = 'exams/candidate_confirm_delete.html'

    def get_entry(self, exam_id, entry_id):
        exam = get_object_or_404(
            Exam.objects.for_tenant(self.request.tenant),
            pk=exam_id
        )
        return get_object_or_404(
            ExamParticipantRoster.objects.filter(exam=exam).select_related('participant'),
            pk=entry_id
        )

    def get(self, request, exam_id, entry_id, *args, **kwargs):
        entry = self.get_entry(exam_id, entry_id)
        return render(request, self.template_name, {
            'exam': entry.exam,
            'entry': entry
        })

    def post(self, request, exam_id, entry_id, *args, **kwargs):
        entry = self.get_entry(exam_id, entry_id)
        candidate_name = entry.participant.get_full_name() or entry.participant.username
        blind_idx = entry.candidate_index
        exam_pk = entry.exam.pk

        with transaction.atomic():
            entry.delete()
            # Re-sequence remaining candidate indices sequentially
            remaining = ExamParticipantRoster.objects.filter(exam_id=exam_pk).order_by('candidate_index')
            for new_idx, item in enumerate(remaining, start=1):
                if item.candidate_index != new_idx:
                    item.candidate_index = new_idx
                    item.save(update_fields=['candidate_index'])

        messages.success(request, f"Candidate #{blind_idx:03d} ({candidate_name}) removed from roster. Blind indices re-sequenced.")
        return redirect('exams:roster_hub', exam_id=exam_pk)


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
