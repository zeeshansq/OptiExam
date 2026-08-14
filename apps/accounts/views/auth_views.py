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

# Initial Role Dashboards (Foundation / Phase 1)
class DesignerDashboardView(DesignerRequiredMixin, TemplateView):
    template_name = 'dashboards/designer.html'

class ItemWriterDashboardView(ItemWriterRequiredMixin, TemplateView):
    template_name = 'dashboards/item_writer.html'

class GraderDashboardView(GraderRequiredMixin, TemplateView):
    template_name = 'dashboards/grader.html'

class ParticipantDashboardView(ParticipantRequiredMixin, TemplateView):
    template_name = 'dashboards/participant.html'
