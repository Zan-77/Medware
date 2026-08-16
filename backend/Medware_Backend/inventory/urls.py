from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InventoryCategoryViewSet, InventoryItemViewSet, SupplierBillViewSet, SupplierBillLineViewSet, StockEntryViewSet
)

router = DefaultRouter()
router.register(r'categories', InventoryCategoryViewSet)
router.register(r'items', InventoryItemViewSet)
router.register(r'bills', SupplierBillViewSet)
router.register(r'bill-lines', SupplierBillLineViewSet)
router.register(r'stock-entries', StockEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
