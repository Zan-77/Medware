from rest_framework import viewsets, permissions
from .models import Voucher, PaymentRecord, CommissionRecord, CustomerBalance
from .serializers import (
    VoucherSerializer, PaymentRecordSerializer, CommissionRecordSerializer, CustomerBalanceSerializer
)
from users.permissions import RoleMethodPermission


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        'POST': ['SALESMAN', 'ACCOUNTANT'],
        'PUT': ['ACCOUNTANT', 'MANAGER'],
        'PATCH': ['ACCOUNTANT', 'MANAGER'],
        'DELETE': ['MANAGER'],
    }


class PaymentRecordViewSet(viewsets.ModelViewSet):
    queryset = PaymentRecord.objects.all()
    serializer_class = PaymentRecordSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['SALESMAN', 'ACCOUNTANT'],
        'PUT': ['ACCOUNTANT'],
        'PATCH': ['ACCOUNTANT'],
        'DELETE': ['MANAGER'],
    }


class CommissionRecordViewSet(viewsets.ModelViewSet):
    queryset = CommissionRecord.objects.all()
    serializer_class = CommissionRecordSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        'POST': ['ACCOUNTANT'],
        'PUT': ['ACCOUNTANT'],
        'PATCH': ['ACCOUNTANT'],
        'DELETE': ['MANAGER'],
    }


class CustomerBalanceViewSet(viewsets.ModelViewSet):
    queryset = CustomerBalance.objects.all()
    serializer_class = CustomerBalanceSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'POST': ['ACCOUNTANT'],
        'PUT': ['ACCOUNTANT'],
        'PATCH': ['ACCOUNTANT'],
        'DELETE': ['MANAGER'],
    }
