from rest_framework import viewsets, permissions
from .models import WebsiteCustomerProfile, WebsiteCatalog, WebsiteCatalogItem
from .serializers import WebsiteCustomerProfileSerializer, WebsiteCatalogSerializer, WebsiteCatalogItemSerializer
from users.permissions import RoleMethodPermission


class WebsiteCustomerProfileViewSet(viewsets.ModelViewSet):
    queryset = WebsiteCustomerProfile.objects.all()
    serializer_class = WebsiteCustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'CUSTOMER'],
        'POST': ['GUEST', 'CUSTOMER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
    }


class WebsiteCatalogViewSet(viewsets.ModelViewSet):
    queryset = WebsiteCatalog.objects.all()
    serializer_class = WebsiteCatalogSerializer
    permission_classes = [permissions.AllowAny]
    # Only manager can modify catalogs
    allowed_roles_by_method = {
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class WebsiteCatalogItemViewSet(viewsets.ModelViewSet):
    queryset = WebsiteCatalogItem.objects.all()
    serializer_class = WebsiteCatalogItemSerializer
    permission_classes = [permissions.AllowAny]
    allowed_roles_by_method = {
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }
