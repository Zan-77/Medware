from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderRequestViewSet, OrderItemViewSet, OrderReviewViewSet, OrderFinalizationViewSet,
    PackagingTaskViewSet, ReturnRequestViewSet, ReturnAssessmentViewSet, ReturnApprovalViewSet,
    InboxView
)

router = DefaultRouter()
router.register(r'order-requests', OrderRequestViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'reviews', OrderReviewViewSet)
router.register(r'finalizations', OrderFinalizationViewSet)
router.register(r'packaging', PackagingTaskViewSet)
router.register(r'return-requests', ReturnRequestViewSet)
router.register(r'return-assessments', ReturnAssessmentViewSet)
router.register(r'return-approvals', ReturnApprovalViewSet)

urlpatterns = [
    path('inbox/', InboxView.as_view(), name='order-inbox'),
    path('', include(router.urls)),
]
