from rest_framework import serializers
from .models import  Supplier, Product, Bill, Archive, Order, OrderProduct, ProductSupplier, Voucher, OrderVoucher

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'phone']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'whole_price', 'retail_price', 'name', 'image_url']

class BillSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Bill
        fields = ['id', 'supplier', 'supplier_name', 'date']

class ArchiveSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    salesman_name = serializers.CharField(source='salesman.name', read_only=True)
    
    class Meta:
        model = Archive
        fields = ['id', 'customer', 'customer_name', 'salesman', 'salesman_name']

class OrderProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderProduct
        fields = ['id', 'order', 'product', 'product_name', 'quantity', 'sell_price', 'return_quantity']

class OrderSerializer(serializers.ModelSerializer):
    order_products = OrderProductSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'archive', 'date', 'packaging_date', 'recieve_date', 'salesman_rate', 'order_products']

class ProductSupplierSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductSupplier
        fields = ['id', 'product', 'product_name', 'bill', 'category', 'quantity', 'discount']

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['id', 'value', 'date', 'salesman_value']

class OrderVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderVoucher
        fields = ['id', 'order', 'voucher']