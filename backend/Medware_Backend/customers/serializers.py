from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'address', 'notes', 'user', 'created_at',
            'status', 'created_by', 'created_by_name', 'rejection_notes',
        ]
        # `status` moves only through the approve/reject actions; leaving it
        # writable would let a salesman approve their own customer with a POST.
        read_only_fields = ['created_at', 'status', 'created_by', 'rejection_notes']
