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
            and not getattr(request.user, 'requires_relogin', False)
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