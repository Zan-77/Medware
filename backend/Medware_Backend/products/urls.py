from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet, ProductViewSet, BillViewSet,
    ArchiveViewSet, OrderViewSet, OrderProductViewSet,
    ProductSupplierViewSet, VoucherViewSet, OrderVoucherViewSet
)

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'bills', BillViewSet)
router.register(r'archives', ArchiveViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-products', OrderProductViewSet)
router.register(r'product-suppliers', ProductSupplierViewSet)
router.register(r'vouchers', VoucherViewSet)
router.register(r'order-vouchers', OrderVoucherViewSet)

urlpatterns = [
    path('', include(router.urls)),
]