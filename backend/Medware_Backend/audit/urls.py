from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, RequestTransitionViewSet

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'request-transitions', RequestTransitionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
