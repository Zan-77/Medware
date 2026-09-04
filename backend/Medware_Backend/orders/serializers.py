from rest_framework import serializers
from .models import OrderRequest, OrderItem, OrderReview, OrderFinalization, PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order_request', 'product', 'quantity', 'sell_price', 'note', 'return_quantity']
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

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        order = OrderRequest.objects.create(**validated_data)
        for item in items:
            OrderItem.objects.create(order_request=order, **item)
        return order


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
