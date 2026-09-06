from rest_framework import serializers

from customers.models import Customer

from .models import Voucher, PaymentRecord, CommissionRecord, CustomerBalance
from .services import salesman_display, salesman_for_customer


class VoucherSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True, default=None)
    salesman_name = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = [
            'id', 'number', 'date', 'customer', 'customer_name',
            'order', 'salesman', 'salesman_name', 'amount', 'reference',
        ]
        # The salesman is the one who raised the customer's order. Accepting it
        # from the request body would let the entry disagree with the order it
        # is paying for.
        read_only_fields = ['salesman']

    def get_salesman_name(self, voucher):
        return salesman_display(voucher.salesman)

    def validate_customer(self, value):
        if value.status != Customer.Status.APPROVED:
            raise serializers.ValidationError(
                'This customer cannot have payments recorded against them yet.')
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('A voucher must be for a positive amount.')
        return value

    def validate_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A voucher number is required.')
        return value

    def validate(self, attrs):
        # A voucher may name one order, but only one of that customer's own -
        # otherwise the statement shows a payment against somebody else's order.
        order = attrs.get('order') or getattr(self.instance, 'order', None)
        customer = attrs.get('customer') or getattr(self.instance, 'customer', None)
        if order is not None and customer is not None and order.customer_id != customer.pk:
            raise serializers.ValidationError({
                'order': 'That order belongs to a different customer.',
            })
        return attrs

    def create(self, validated_data):
        # Derived here rather than in the view so it holds for every caller.
        validated_data['salesman'] = salesman_for_customer(validated_data['customer'])
        return super().create(validated_data)


class CustomerAccountSerializer(serializers.Serializer):
    """One row of the finance panel: who owes what.

    Read-only by design - the figures come from orders and vouchers, so there
    is nothing here to write. Expects the annotations from
    `services.customer_accounts()` and a `salesman_name` attached by the view.
    """

    customer = serializers.IntegerField(source='id', read_only=True)
    customer_name = serializers.CharField(source='name', read_only=True)
    phone = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    salesman_name = serializers.CharField(read_only=True, default=None)
    total_ordered = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_paid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    outstanding = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)


class StatementOrderSerializer(serializers.Serializer):
    """An order as it appears on a statement - what raised the balance."""

    id = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(source='created_at', read_only=True)
    status = serializers.CharField(read_only=True)
    total = serializers.DecimalField(source='line_total', max_digits=14,
                                     decimal_places=2, read_only=True)
    salesman_name = serializers.SerializerMethodField()

    def get_salesman_name(self, order):
        return salesman_display(order.salesman)


class StatementVoucherSerializer(serializers.ModelSerializer):
    """A voucher as it appears on a statement - what lowered the balance."""

    class Meta:
        model = Voucher
        fields = ['id', 'number', 'date', 'amount', 'reference', 'order']


class PaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = '__all__'


class CommissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRecord
        fields = '__all__'


class CustomerBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerBalance
        fields = '__all__'
