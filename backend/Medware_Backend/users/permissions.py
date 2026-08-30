# users/permissions.py
# Custom permission class for DRF-compatible projects.
# If Django REST Framework is not installed, this file remains importable.

try:
    from rest_framework.permissions import BasePermission
except ImportError:
    BasePermission = object

class HasRole(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )

class IsManager(HasRole):
    allowed_roles = ['MANAGER']

class IsAccountant(HasRole):
    allowed_roles = ['ACCOUNTANT']

class IsSalesman(HasRole):
    allowed_roles = ['SALESMAN']

class IsCustomer(HasRole):
    allowed_roles = ['CUSTOMER']

class IsAccountantOrManager(HasRole):
    allowed_roles = ['ACCOUNTANT', 'MANAGER']


class RoleMethodPermission(BasePermission):
    """
    Permission that enforces allowed roles per HTTP method on a view.

    Views may define `allowed_roles_by_method` as a dict mapping HTTP method
    names (e.g. 'GET', 'POST', 'PUT', 'PATCH', 'DELETE') to lists of role keys.

    This permission is default-deny: a method that is not listed in the
    mapping is refused, and a view that declares no mapping at all refuses
    everything. Anything a role should be able to do must be stated
    explicitly. Superusers bypass role checks.

    HEAD and OPTIONS are evaluated against the 'GET' entry, so read access
    implies the ability to probe the endpoint.
    """

    def has_permission(self, request, view):
        # Require authentication first
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False

        if getattr(request.user, 'is_superuser', False):
            return True

        mapping = getattr(view, 'allowed_roles_by_method', None)
        if not mapping:
            # Default deny: a view opting into role checks must declare them.
            return False

        method = request.method
        if method in ('HEAD', 'OPTIONS'):
            method = 'GET'

        allowed = mapping.get(method)
        if allowed is None:
            # Method not declared for this view -> refused.
            return False

        return request.user.role in allowed

    def has_object_permission(self, request, view, obj):
        # Default to same check as has_permission; views can override.
        return self.has_permission(request, view)


class PublicReadRoleWritePermission(RoleMethodPermission):
    """Anonymous read, role-checked write.

    For genuinely public content (the storefront catalogue) where reads must
    work for signed-out visitors but every write still has to satisfy the
    view's `allowed_roles_by_method` entry.
    """

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return super().has_permission(request, view)