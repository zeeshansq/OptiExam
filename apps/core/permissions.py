class BasePermission:
    """Base class from which all permission classes should inherit."""
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin()

class IsTenantDesigner(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_designer() or request.user.is_super_admin())
            and (request.tenant is None or request.user.tenant == request.tenant or request.user.is_super_admin())
        )

class IsItemWriter(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_item_writer() or request.user.is_designer() or request.user.is_super_admin())
        )

class IsGrader(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_grader() or request.user.is_super_admin())
        )

class IsParticipant(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.is_participant() or request.user.is_super_admin())
        )
