# users/permissions.py
# Custom permission class for DRF-compatible projects.
# If Django REST Framework is not installed, this file remains importable.

try:
    from rest_framework.permissions import BasePermission
except ImportError:
    BasePermission = object

# The single definition of which roles carry staff privileges. serializers.py
# imports this rather than keeping its own copy - two hand-maintained lists of
# "which roles are privileged" drift, and the one that drifts is a hole.
STAFF_ROLES = {'MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER'}


def staff_account_is_unverified(user):
    """True when this account holds a staff role a manager has not approved.

    Customers are exempt: the storefront lets them self-register, and holding
    them behind manual approval would block it. Superusers bypass entirely.

    Read from the row, never from the JWT claim - the access token lives 15
    minutes, so a claim would leave someone locked out that long after a
    manager approves them.
    """
    if getattr(user, 'is_superuser', False):
        return False
    return (
        getattr(user, 'role', None) in STAFF_ROLES
        and not getattr(user, 'is_verified', False)
    )


class HasRole(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if staff_account_is_unverified(request.user):
            return False
        return request.user.role in self.allowed_roles

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

        # A staff role does not take effect until a manager approves the
        # account. Checked against the row, not the token claim.
        if staff_account_is_unverified(request.user):
            return False

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