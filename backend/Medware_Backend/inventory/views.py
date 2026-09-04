from rest_framework import viewsets, permissions
from .models import InventoryCategory, InventoryItem, SupplierBill, SupplierBillLine, StockEntry
from .serializers import (
    InventoryCategorySerializer, InventoryItemSerializer, SupplierBillSerializer,
    SupplierBillLineSerializer, StockEntrySerializer
)
from users.permissions import RoleMethodPermission
from mysite.filters import filter_by_query_params


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

    def get_queryset(self):
        # `?category=` backs the category drill-down; `?product=` resolves the
        # inventory row for a catalogue product.
        return filter_by_query_params(
            super().get_queryset(), self.request,
            {'category': 'category_id', 'product': 'product_id'},
        )


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

    def get_queryset(self):
        # `?supplier=` is how the suppliers table opens "the bills of this
        # supplier"; without it that link listed every bill in the system.
        return filter_by_query_params(
            super().get_queryset(), self.request,
            {'supplier': 'supplier_id', 'manager': 'manager_id', 'id': 'id'},
        )


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

    def get_queryset(self):
        # `?bill=` is the whole point of the bill-details page: one bill's
        # lines, not every line ever recorded.
        return filter_by_query_params(
            super().get_queryset(), self.request,
            {'bill': 'bill_id', 'item': 'item_id', 'category': 'category_id'},
        )


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

    def get_queryset(self):
        return filter_by_query_params(
            super().get_queryset(), self.request,
            {'item': 'item_id', 'source_bill_line': 'source_bill_line_id'},
        )
