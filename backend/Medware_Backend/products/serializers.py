from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from .models import Supplier, Product, ProductSupplier

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'phone']

class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    def _inventory_category(self, product):
        try:
            item = product.inventory_item
        except ObjectDoesNotExist:
            item = None
        return item.category if item else None

    def get_category_id(self, product):
        category = self._inventory_category(product)
        return category.id if category else None

    def get_category_name(self, product):
        category = self._inventory_category(product)
        return category.name if category else 'Uncategorized'

    class Meta:
        model = Product
        fields = [
            'id', 'whole_price', 'retail_price', 'name', 'image_url',
            'category_id', 'category_name',
        ]

class ProductSupplierSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = ProductSupplier
        # `product_name` is declared above, so it must be listed here too -
        # DRF raises an AssertionError (surfacing as a 500) on any request
        # that builds this serializer's fields if it is missing.
        fields = ['id', 'product', 'product_name', 'supplier', 'supplier_name', 'discount']