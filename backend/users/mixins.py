# users/mixins.py
# A mixin for class-based views that checks if the user has one of the allowed roles before allowing access.
# It returns JSON error responses for API-friendly handling.

from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return JsonResponse({'detail': 'Authentication required.'}, status=401)
        return JsonResponse({'detail': 'Permission denied.'}, status=403)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role not in self.allowed_roles:
            return JsonResponse({'detail': 'Permission denied.'}, status=403)
        return super().dispatch(request, *args, **kwargs)