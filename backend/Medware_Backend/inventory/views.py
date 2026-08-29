from rest_framework import viewsets, permissions
from .models import InventoryCategory, InventoryItem, SupplierBill, SupplierBillLine, StockEntry
from .serializers import (
    InventoryCategorySerializer, InventoryItemSerializer, SupplierBillSerializer,
    SupplierBillLineSerializer, StockEntrySerializer
)
from users.permissions import RoleMethodPermission


class InventoryCategoryViewSet(viewsets.ModelViewSet):
    queryset = InventoryCategory.objects.all()
    serializer_class = InventoryCategorySerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class SupplierBillViewSet(viewsets.ModelViewSet):
    queryset = SupplierBill.objects.all()
    serializer_class = SupplierBillSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class SupplierBillLineViewSet(viewsets.ModelViewSet):
    queryset = SupplierBillLine.objects.all()
    serializer_class = SupplierBillLineSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class StockEntryViewSet(viewsets.ModelViewSet):
    queryset = StockEntry.objects.all()
    serializer_class = StockEntrySerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'WAREHOUSE_WORKER'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }
