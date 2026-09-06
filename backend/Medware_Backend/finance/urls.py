from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VoucherViewSet, PaymentRecordViewSet, CommissionRecordViewSet,
    CustomerBalanceViewSet, CustomerAccountViewSet,
)

router = DefaultRouter()
router.register(r'vouchers', VoucherViewSet)
router.register(r'payments', PaymentRecordViewSet)
router.register(r'commissions', CommissionRecordViewSet)
router.register(r'balances', CustomerBalanceViewSet)
# Derived from orders and vouchers, unlike `balances` above, which reads the
# stored CustomerBalance table nothing currently maintains.
router.register(r'customer-accounts', CustomerAccountViewSet, basename='customer-account')

urlpatterns = [
    path('', include(router.urls)),
]
