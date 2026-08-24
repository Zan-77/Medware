from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet, ProductViewSet,
    ProductSupplierViewSet
)

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-suppliers', ProductSupplierViewSet)

urlpatterns = [
    path('', include(router.urls)),
]