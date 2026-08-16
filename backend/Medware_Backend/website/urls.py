from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteCustomerProfileViewSet, WebsiteCatalogViewSet, WebsiteCatalogItemViewSet

router = DefaultRouter()
router.register(r'customers', WebsiteCustomerProfileViewSet)
router.register(r'catalogs', WebsiteCatalogViewSet)
router.register(r'catalog-items', WebsiteCatalogItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
