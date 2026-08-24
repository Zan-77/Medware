from rest_framework import serializers
from .models import Supplier, Product, ProductSupplier

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'phone']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'whole_price', 'retail_price', 'name', 'image_url']

class ProductSupplierSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductSupplier
        fields = ['id', 'product', 'discount']