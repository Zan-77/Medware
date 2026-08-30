from rest_framework import permissions, viewsets
from .models import WebsiteCustomerProfile, WebsiteCatalog, WebsiteCatalogItem
from .serializers import WebsiteCustomerProfileSerializer, WebsiteCatalogSerializer, WebsiteCatalogItemSerializer
from users.permissions import PublicReadRoleWritePermission, RoleMethodPermission


class WebsiteCustomerProfileViewSet(viewsets.ModelViewSet):
    queryset = WebsiteCustomerProfile.objects.all()
    serializer_class = WebsiteCustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'CUSTOMER'],
        'POST': ['GUEST', 'CUSTOMER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # A customer/guest may only ever see their own profile row.
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or user.role in ('MANAGER', 'ACCOUNTANT', 'SALESMAN'):
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        # `user` is never taken from the request body - see serializer.
        serializer.save(user=self.request.user)


class WebsiteCatalogViewSet(viewsets.ModelViewSet):
    queryset = WebsiteCatalog.objects.all()
    serializer_class = WebsiteCatalogSerializer
    # Storefront catalogue: readable by anonymous visitors, manager-only writes.
    permission_classes = [PublicReadRoleWritePermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER', 'GUEST'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class WebsiteCatalogItemViewSet(viewsets.ModelViewSet):
    queryset = WebsiteCatalogItem.objects.all()
    serializer_class = WebsiteCatalogItemSerializer
    permission_classes = [PublicReadRoleWritePermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER', 'GUEST'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }
