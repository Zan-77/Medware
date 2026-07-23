from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from django.utils import timezone

from .models import Category, Supplier, SupplierCategory, Product, Bill, BillItem, Inventory
from .serializers import (
    CategorySerializer, SupplierSerializer, SupplierCategorySerializer,
    ProductSerializer, BillSerializer, BillDetailedSerializer, BillItemSerializer, InventorySerializer
)
from users.permissions import IsManager


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.prefetch_related('supplied_categories').all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'city', 'country']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'])
    def categories(self, request, pk=None):
        """Get all categories supplied by this supplier."""
        supplier = self.get_object()
        categories = supplier.supplied_categories.filter(is_active=True)
        serializer = SupplierCategorySerializer(categories, many=True)
        return Response(serializer.data)


class SupplierCategoryViewSet(viewsets.ModelViewSet):
    queryset = SupplierCategory.objects.select_related('supplier', 'category')
    serializer_class = SupplierCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'supplier__name', 'category__name']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Filter supplier-category mappings by category."""
        category_id = request.query_params.get('category_id')
        if category_id:
            qs = self.get_queryset().filter(category_id=category_id)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response({'error': 'category_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_supplier(self, request):
        """Filter supplier-category mappings by supplier."""
        supplier_id = request.query_params.get('supplier_id')
        if supplier_id:
            qs = self.get_queryset().filter(supplier_id=supplier_id)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response({'error': 'supplier_id required'}, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'category__name']
    ordering_fields = ['name', 'sku', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsManager]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get products by category."""
        category_id = request.query_params.get('category_id')
        if category_id:
            qs = self.get_queryset().filter(category_id=category_id)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response({'error': 'category_id required'}, status=status.HTTP_400_BAD_REQUEST)


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bill_number', 'supplier__name']
    ordering_fields = ['bill_date', 'status', 'created_at']
    ordering = ['-bill_date']

    def get_queryset(self):
        return Bill.objects.prefetch_related(
            'items__product',
            'supplier'
        ).select_related('created_by').all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BillDetailedSerializer
        return BillSerializer

    def perform_create(self, serializer):
        """Auto-set created_by to current user."""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_supplier(self, request):
        """Get bills by supplier with optional date filtering."""
        supplier_id = request.query_params.get('supplier_id')
        if not supplier_id:
            return Response({'error': 'supplier_id required'}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(supplier_id=supplier_id)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            qs = qs.filter(bill_date__gte=start_date)
        if end_date:
            qs = qs.filter(bill_date__lte=end_date)
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get bills that contain a specific category."""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response({'error': 'category_id required'}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(
            items__product__category_id=category_id
        ).distinct()

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_received(self, request, pk=None):
        """Mark a bill as received."""
        bill = self.get_object()
        if bill.status != Bill.Status.ORDERED:
            return Response(
                {'error': 'Only ordered bills can be marked as received.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        bill.status = Bill.Status.RECEIVED
        bill.save()
        serializer = self.get_serializer(bill)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get supplier and category history for this bill."""
        bill = self.get_object()
        supplier = bill.supplier
        
        supplier_bills = self.get_queryset().filter(supplier=supplier).count()
        categories = bill.items.values_list('product__category', flat=True).distinct()
        
        return Response({
            'bill': BillDetailedSerializer(bill).data,
            'supplier_total_bills': supplier_bills,
            'categories_in_bill': categories,
        })


class BillItemViewSet(viewsets.ModelViewSet):
    queryset = BillItem.objects.select_related('bill', 'product')
    serializer_class = BillItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def get_queryset(self):
        bill_id = self.request.query_params.get('bill_id')
        qs = self.get_queryset()
        if bill_id:
            qs = qs.filter(bill_id=bill_id)
        return qs

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create bill items."""
        items_data = request.data.get('items', [])
        bill_id = request.data.get('bill_id')
        
        if not bill_id:
            return Response({'error': 'bill_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bill = Bill.objects.get(id=bill_id)
        except Bill.DoesNotExist:
            return Response({'error': 'Bill not found'}, status=status.HTTP_404_NOT_FOUND)

        created_items = []
        for item_data in items_data:
            item_data['bill'] = bill_id
            serializer = self.get_serializer(data=item_data)
            if serializer.is_valid():
                serializer.save()
                created_items.append(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bill.calculate_total()
        bill.save()

        return Response({'created_items': created_items, 'bill_total': str(bill.total_amount)})


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Inventory.objects.select_related('product__category')
    serializer_class = InventorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product__name', 'product__sku']
    ordering_fields = ['quantity', 'reorder_level', 'updated_at']
    ordering = ['product__name']

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products below reorder level."""
        qs = self.get_queryset().filter(quantity__lte=F('reorder_level'))
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get inventory by category."""
        category_id = request.query_params.get('category_id')
        if category_id:
            qs = self.get_queryset().filter(product__category_id=category_id)
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return Response({'error': 'category_id required'}, status=status.HTTP_400_BAD_REQUEST)

