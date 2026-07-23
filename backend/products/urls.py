from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (
    CategoryViewSet, SupplierViewSet, SupplierCategoryViewSet,
    ProductViewSet, BillViewSet, BillItemViewSet, InventoryViewSet
)

router = SimpleRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'supplier-categories', SupplierCategoryViewSet, basename='supplier-category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'bill-items', BillItemViewSet, basename='bill-item')
router.register(r'inventory', InventoryViewSet, basename='inventory')

urlpatterns = [
    path('', include(router.urls)),
]
