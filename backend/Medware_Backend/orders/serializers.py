from rest_framework import serializers
from .models import OrderRequest, OrderItem, OrderReview, OrderFinalization, PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, default=None)

    class Meta:
        model = OrderItem
        fields = ['id', 'order_request', 'product', 'product_name', 'quantity', 'sell_price', 'note', 'return_quantity']
        extra_kwargs = {'order_request': {'required': False}}


class OrderRequestSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default=None)
    salesman_name = serializers.CharField(source='salesman.username', read_only=True, default=None)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderRequest
        fields = [
            'id', 'origin', 'customer', 'customer_name', 'salesman', 'salesman_name',
            'created_at', 'status', 'notes', 'previous_balance', 'new_balance',
            'total', 'items',
        ]
        # `status` moves only through the approve/reject actions. `origin` and
        # `salesman` are derived from the requesting user. Leaving any of them
        # writable lets a salesman approve their own order with a PATCH.
        read_only_fields = ['status', 'origin', 'salesman', 'previous_balance', 'new_balance']

    def validate_customer(self, value):
        # An order approved against a customer the company has not accepted is
        # a record nobody can act on. The manager sees the customer request in
        # the same inbox, so the wait is short.
        from customers.models import Customer

        if value.status != Customer.Status.APPROVED:
            raise serializers.ValidationError(
                f'This customer is {value.status} and cannot have orders raised for them yet.')
        return value

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        order = OrderRequest.objects.create(**validated_data)
        for item in items:
            # The parent order always wins; a nested item that carries its own
            # `order_request` would otherwise raise TypeError -> 500.
            item.pop('order_request', None)
            OrderItem.objects.create(order_request=order, **item)
        return order

    def update(self, instance, validated_data):
        # Items are edited through /api/orders/order-items/, not nested here.
        # Without this, a PATCH carrying `items` hits DRF's nested-write
        # assertion and returns 500 instead of a validation error.
        if 'items' in validated_data:
            raise serializers.ValidationError({
                'items': 'Order items are edited through /api/orders/order-items/.',
            })
        return super().update(instance, validated_data)


class OrderReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReview
        fields = '__all__'


class OrderFinalizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderFinalization
        fields = '__all__'


class PackagingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagingTask
        fields = '__all__'


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = '__all__'


class ReturnAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnAssessment
        fields = '__all__'


class ReturnApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnApproval
        fields = '__all__'
