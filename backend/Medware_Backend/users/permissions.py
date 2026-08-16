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

    If a method is not present in the dict, access falls back to allowing
    authenticated users. Superusers bypass role checks.
    """

    def has_permission(self, request, view):
        # Require authentication first
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False

        if getattr(request.user, 'is_superuser', False):
            return True

        mapping = getattr(view, 'allowed_roles_by_method', None)
        if not mapping:
            return True

        allowed = mapping.get(request.method)
        if allowed is None:
            # No restriction for this method
            return True

        return request.user.role in allowed

    def has_object_permission(self, request, view, obj):
        # Default to same check as has_permission; views can override.
        return self.has_permission(request, view)