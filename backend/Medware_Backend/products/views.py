from rest_framework import viewsets, permissions
from .models import Supplier, Product, ProductSupplier
from .serializers import (
    SupplierSerializer, ProductSerializer,
    ProductSupplierSerializer
)
from users.permissions import RoleMethodPermission
from mysite.filters import filter_by_query_params

# The product catalogue is readable by every signed-in role (the storefront
# and the internal app both list it), but only a manager may change it.
CATALOGUE_ROLES = ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER', 'GUEST']


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        # Supplier records are internal - not exposed to customers/guests.
        'GET': ['MANAGER', 'ACCOUNTANT', 'WAREHOUSE_WORKER'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # `?id=` backs `getSuppliersById`, which resolves one supplier's name
        # for a bills table cell.
        return filter_by_query_params(super().get_queryset(), self.request, {'id': 'id'})


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': CATALOGUE_ROLES,
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class ProductSupplierViewSet(viewsets.ModelViewSet):
    queryset = ProductSupplier.objects.all()
    serializer_class = ProductSupplierSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'WAREHOUSE_WORKER'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # `?supplier=` backs the supplier-details table of a supplier's products.
        return filter_by_query_params(
            super().get_queryset(), self.request,
            {'supplier': 'supplier_id', 'product': 'product_id'},
        )
