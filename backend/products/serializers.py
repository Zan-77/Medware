from rest_framework import serializers
from .models import Category, Supplier, SupplierCategory, Product, Bill, BillItem, Inventory


class CategorySerializer(serializers.ModelSerializer):
    supplier_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'supplier_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_supplier_count(self, obj):
        return obj.suppliers.count()


class SupplierSerializer(serializers.ModelSerializer):
    category_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone',
            'address', 'city', 'country', 'tax_id', 'is_active',
            'category_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_category_count(self, obj):
        return obj.supplied_categories.count()


class SupplierCategorySerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = SupplierCategory
        fields = ['id', 'supplier', 'supplier_name', 'category', 'category_name', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    current_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name', 'description',
            'sku', 'unit', 'is_active', 'current_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_current_stock(self, obj):
        if hasattr(obj, 'inventory'):
            return obj.inventory.quantity
        return 0


class BillItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_unit = serializers.CharField(source='product.unit', read_only=True)

    class Meta:
        model = BillItem
        fields = [
            'id', 'bill', 'product', 'product_name', 'product_unit',
            'quantity', 'unit_price', 'total_price', 'batch_number',
            'size', 'expiry_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_price', 'created_at', 'updated_at']


class BillSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'supplier', 'supplier_name', 'bill_number', 'bill_date',
            'status', 'status_display', 'notes', 'total_amount',
            'created_by', 'created_by_username', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount', 'created_by', 'created_at', 'updated_at']


class BillDetailedSerializer(BillSerializer):
    """Detailed bill serializer with full supplier and category history."""
    supplier_details = SupplierSerializer(source='supplier', read_only=True)
    supplier_categories = serializers.SerializerMethodField()

    class Meta(BillSerializer.Meta):
        fields = BillSerializer.Meta.fields + ['supplier_details', 'supplier_categories']

    def get_supplier_categories(self, obj):
        categories = obj.supplier.supplied_categories.filter(is_active=True)
        return SupplierCategorySerializer(categories, many=True).data


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    category_name = serializers.CharField(source='product.category.name', read_only=True)
    below_reorder = serializers.SerializerMethodField()

    class Meta:
        model = Inventory
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'category_name',
            'quantity', 'reorder_level', 'below_reorder', 'last_restocked', 'updated_at'
        ]
        read_only_fields = ['product', 'last_restocked', 'updated_at']

    def get_below_reorder(self, obj):
        return obj.quantity <= obj.reorder_level
