from rest_framework import mixins, permissions, viewsets
from .models import AuditLog, RequestTransition
from .serializers import AuditLogSerializer, RequestTransitionSerializer
from users.permissions import RoleMethodPermission


class AppendOnlyViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """List/retrieve/create only.

    An audit trail that can be edited or deleted through the API is not an
    audit trail, so PUT/PATCH/DELETE are deliberately not routed here and
    return 405. This is intentional, not an oversight.
    """
    pass


class AuditLogViewSet(AppendOnlyViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['MANAGER', 'ACCOUNTANT'],
    }


class RequestTransitionViewSet(AppendOnlyViewSet):
    queryset = RequestTransition.objects.all()
    serializer_class = RequestTransitionSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['MANAGER', 'ACCOUNTANT'],
    }
