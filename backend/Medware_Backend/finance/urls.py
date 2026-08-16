from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VoucherViewSet, PaymentRecordViewSet, CommissionRecordViewSet, CustomerBalanceViewSet

router = DefaultRouter()
router.register(r'vouchers', VoucherViewSet)
router.register(r'payments', PaymentRecordViewSet)
router.register(r'commissions', CommissionRecordViewSet)
router.register(r'balances', CustomerBalanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
