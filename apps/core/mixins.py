from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from apps.accounts.models import UserRole

class SuperAdminRequiredMixin(AccessMixin):
    """Verify that the current user has SUPER_ADMIN role."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_super_admin():
            raise PermissionDenied("Access restricted to SaaS Super Administrators.")
        return super().dispatch(request, *args, **kwargs)

class DesignerRequiredMixin(AccessMixin):
    """Verify that the current user is a DESIGNER (Tenant Admin) for the active tenant."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_designer() or request.user.is_super_admin()):
            raise PermissionDenied("Access restricted to Examination Designers.")
        if request.tenant and request.user.tenant != request.tenant and not request.user.is_super_admin():
            raise PermissionDenied("You do not have administrative access to this institution.")
        return super().dispatch(request, *args, **kwargs)

class ItemWriterRequiredMixin(AccessMixin):
    """Verify that the current user is an ITEM_WRITER or DESIGNER."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_item_writer() or request.user.is_designer() or request.user.is_super_admin()):
            raise PermissionDenied("Access restricted to Item Writers and Designers.")
        return super().dispatch(request, *args, **kwargs)

class GraderRequiredMixin(AccessMixin):
    """Verify that the current user is a GRADER."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_grader() or request.user.is_super_admin()):
            raise PermissionDenied("Access restricted to Examination Graders.")
        return super().dispatch(request, *args, **kwargs)

class ParticipantRequiredMixin(AccessMixin):
    """Verify that the current user is a PARTICIPANT."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_participant() or request.user.is_super_admin()):
            raise PermissionDenied("Access restricted to Examination Candidates.")
        return super().dispatch(request, *args, **kwargs)

class TenantStaffRequiredMixin(AccessMixin):
    """Verify that the current user is staff (Designer, Item Writer, Grader)."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role == UserRole.PARTICIPANT and not request.user.is_super_admin():
            raise PermissionDenied("Access restricted to Faculty & Staff members.")
        return super().dispatch(request, *args, **kwargs)
