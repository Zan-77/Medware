from django.utils import timezone
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only over the API - rows are created by workflow transitions."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Scoped to the requesting user, so a 404 (not a 403) is what someone
        # gets for another user's row - we do not confirm it exists.
        queryset = Notification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get('unread') == 'true':
            queryset = queryset.filter(read_at__isnull=True)
        return queryset

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])
        return Response(self.get_serializer(notification).data)
