from rest_framework import serializers
from .models import Voucher, PaymentRecord, CommissionRecord, CustomerBalance


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'


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
