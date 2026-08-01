from rest_framework import viewsets, permissions
from .models import User, Supplier, Product, Bill, Archive, Order, OrderProduct, ProductSupplier, Voucher, OrderVoucher, Notification
from .serializers import (
    SupplierSerializer, ProductSerializer, BillSerializer,
    ArchiveSerializer, OrderSerializer, OrderProductSerializer,
    ProductSupplierSerializer, VoucherSerializer, OrderVoucherSerializer
)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [permissions.AllowAny]

class ArchiveViewSet(viewsets.ModelViewSet):
    queryset = Archive.objects.all()
    serializer_class = ArchiveSerializer
    permission_classes = [permissions.AllowAny]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]

class OrderProductViewSet(viewsets.ModelViewSet):
    queryset = OrderProduct.objects.all()
    serializer_class = OrderProductSerializer
    permission_classes = [permissions.AllowAny]

class ProductSupplierViewSet(viewsets.ModelViewSet):
    queryset = ProductSupplier.objects.all()
    serializer_class = ProductSupplierSerializer
    permission_classes = [permissions.AllowAny]

class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.AllowAny]

class OrderVoucherViewSet(viewsets.ModelViewSet):
    queryset = OrderVoucher.objects.all()
    serializer_class = OrderVoucherSerializer
    permission_classes = [permissions.AllowAny]