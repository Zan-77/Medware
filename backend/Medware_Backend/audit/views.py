from rest_framework import viewsets, permissions
from .models import AuditLog, RequestTransition
from .serializers import AuditLogSerializer, RequestTransitionSerializer
from users.permissions import RoleMethodPermission


class AuditLogViewSet(viewsets.ModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['MANAGER', 'ACCOUNTANT'],
    }


class RequestTransitionViewSet(viewsets.ModelViewSet):
    queryset = RequestTransition.objects.all()
    serializer_class = RequestTransitionSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['MANAGER', 'ACCOUNTANT'],
    }
