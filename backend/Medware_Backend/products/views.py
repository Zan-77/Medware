from rest_framework import viewsets, permissions
from .models import Supplier, Product, ProductSupplier
from .serializers import (
    SupplierSerializer, ProductSerializer,
    ProductSupplierSerializer
)

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.AllowAny]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class ProductSupplierViewSet(viewsets.ModelViewSet):
    queryset = ProductSupplier.objects.all()
    serializer_class = ProductSupplierSerializer
    permission_classes = [permissions.AllowAny]