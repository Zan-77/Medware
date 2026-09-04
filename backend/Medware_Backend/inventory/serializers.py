from rest_framework import serializers
from .models import InventoryCategory, InventoryItem, SupplierBill, SupplierBillLine, StockEntry


class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = '__all__'


class InventoryItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(read_only=True)
    quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['quantity'] = instance.quantity
        return data


class SupplierBillSerializer(serializers.ModelSerializer):
    # Read-only labels so a table can render "Alpha Supplies" without issuing
    # one lookup per row - the same pattern as ProductSupplierSerializer.
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)

    class Meta:
        model = SupplierBill
        fields = ['id', 'supplier', 'supplier_name', 'manager', 'date', 'notes']


class SupplierBillLineSerializer(serializers.ModelSerializer):
    # `item` and `category` are both SET_NULL, so these must tolerate a null
    # FK rather than blow up on a line whose item was deleted.
    item_name = serializers.CharField(source='item.name', read_only=True, default=None)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = SupplierBillLine
        fields = [
            'id', 'bill', 'item', 'item_name', 'category', 'category_name',
            'quantity', 'expiry_date', 'unit_price', 'discount',
        ]


class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = '__all__'
