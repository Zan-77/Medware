# users/decorators.py
# A decorator for function-based views that checks if the user has one of the allowed roles before allowing access.
# Returns JSON responses for authentication and permission failures.

from functools import wraps
from django.http import JsonResponse

def _authentication_required():
    return JsonResponse({'detail': 'Authentication required.'}, status=401)

def _permission_denied():
    return JsonResponse({'detail': 'Permission denied.'}, status=403)

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return _authentication_required()
            if request.user.role not in allowed_roles:
                return _permission_denied()
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator