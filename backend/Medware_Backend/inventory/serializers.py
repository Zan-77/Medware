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
    class Meta:
        model = SupplierBill
        fields = '__all__'


class SupplierBillLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBillLine
        fields = '__all__'


class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = '__all__'
