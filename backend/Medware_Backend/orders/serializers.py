from rest_framework import serializers
from .models import OrderRequest, OrderItem, OrderReview, OrderFinalization, PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderRequestSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = OrderRequest
        fields = ['id', 'origin', 'customer', 'salesman', 'created_at', 'status', 'notes', 'items']


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
