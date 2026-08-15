from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.forms import OptiExamLoginForm
from apps.accounts.services.auth_service import get_redirect_url_for_user, record_audit_log
from apps.accounts.models import AuditLog
from apps.core.mixins import DesignerRequiredMixin, ItemWriterRequiredMixin, GraderRequiredMixin, ParticipantRequiredMixin

class OptiExamLoginView(DjangoLoginView):
    """
    Universal glassmorphic login view.
    """
    form_class = OptiExamLoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            # Session expires on browser close
            self.request.session.set_expiry(0)
        else:
            # Session persists for 2 weeks (1209600 seconds)
            self.request.session.set_expiry(1209600)

        response = super().form_valid(form)
        user = self.request.user

        # Store tenant slug in session for tenant resolution
        if user.tenant:
            self.request.session['tenant_slug'] = user.tenant.slug

        record_audit_log(
            action=f"User '{user.username}' logged in successfully",
            category=AuditLog.ActionCategory.AUTH,
            user=user,
            tenant=user.tenant,
            request=self.request
        )
        return response

    def form_invalid(self, form):
        username = form.data.get('username')
        record_audit_log(
            action=f"Failed login attempt for username '{username}'",
            category=AuditLog.ActionCategory.SECURITY,
            request=self.request,
            payload={'attempted_username': username}
        )
        return super().form_invalid(form)

class OptiExamLogoutView(DjangoLogoutView):
    """
    Logs out user and clears tenant session metadata.
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            record_audit_log(
                action=f"User '{request.user.username}' logged out",
                category=AuditLog.ActionCategory.AUTH,
                user=request.user,
                tenant=request.user.tenant,
                request=request
            )
        return super().dispatch(request, *args, **kwargs)

class RoleRedirectView(LoginRequiredMixin, RedirectView):
    """
    Redirects authenticated users to their corresponding role dashboard.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return get_redirect_url_for_user(self.request.user)

class DesignerDashboardView(DesignerRequiredMixin, TemplateView):
    template_name = 'dashboards/designer.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.exams.models import Exam
        from apps.questions.models import QuestionBank
        from apps.submissions.models import ExamAttempt

        tenant = self.request.tenant
        ctx['total_exams'] = Exam.objects.for_tenant(tenant).count()
        ctx['total_banks'] = QuestionBank.objects.for_tenant(tenant).count()
        ctx['active_live_attempts'] = ExamAttempt.objects.filter(
            tenant=tenant,
            status=ExamAttempt.Status.IN_PROGRESS,
            is_simulation=False
        ).count()
        ctx['recent_exams'] = Exam.objects.for_tenant(tenant).order_by('-created_at')[:5]
        return ctx


class ItemWriterDashboardView(ItemWriterRequiredMixin, TemplateView):
    template_name = 'dashboards/item_writer.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.questions.models import QuestionBank, Question
        from apps.exams.models import Exam

        tenant = self.request.tenant
        ctx['total_banks'] = QuestionBank.objects.for_tenant(tenant).count()
        ctx['total_questions'] = Question.objects.filter(bank__tenant=tenant).count()
        ctx['available_exams'] = Exam.objects.for_tenant(tenant).order_by('-created_at')[:6]
        return ctx


class GraderDashboardView(GraderRequiredMixin, TemplateView):
    template_name = 'dashboards/grader.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.grading.models import GraderAllocation
        from apps.grading.selectors.grader_selectors import get_grader_allocations

        allocations = get_grader_allocations(self.request.user, tenant=self.request.tenant)
        ctx['allocations'] = allocations
        ctx['total_batches'] = len(allocations)
        ctx['pending_batches'] = sum(1 for a in allocations if a.status != GraderAllocation.Status.COMPLETED)
        return ctx


class ParticipantDashboardView(ParticipantRequiredMixin, TemplateView):
    template_name = 'dashboards/participant.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.exams.models import Exam, ExamParticipantRoster
        from apps.submissions.models import ExamAttempt

        tenant = self.request.tenant
        user = self.request.user

        # Get enrolled exams
        enrolled_exam_ids = ExamParticipantRoster.objects.filter(
            participant=user,
            status=ExamParticipantRoster.Status.ENROLLED
        ).values_list('exam_id', flat=True)

        enrolled_exams = Exam.objects.filter(id__in=enrolled_exam_ids, is_active=True).order_by('start_time')
        
        # Attach active attempt status if any
        exams_with_status = []
        for ex in enrolled_exams:
            att = ExamAttempt.objects.filter(exam=ex, participant=user, is_simulation=False).first()
            exams_with_status.append({
                'exam': ex,
                'attempt': att
            })

        ctx['enrolled_exams'] = exams_with_status
        return ctx

