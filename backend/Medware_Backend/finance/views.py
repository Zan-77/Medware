from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from customers.models import Customer
from mysite.filters import filter_by_query_params
from users.permissions import RoleMethodPermission

from .models import Voucher, PaymentRecord, CommissionRecord, CustomerBalance
from .serializers import (
    VoucherSerializer, PaymentRecordSerializer, CommissionRecordSerializer,
    CustomerBalanceSerializer, CustomerAccountSerializer,
    StatementOrderSerializer, StatementVoucherSerializer,
)
from .services import billable_orders, customer_accounts, latest_salesman_names


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.select_related('customer', 'salesman').all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        # The finance panel that raises vouchers belongs to the accountant and
        # the manager; SALESMAN keeps the access it already had.
        'POST': ['SALESMAN', 'ACCOUNTANT', 'MANAGER'],
        'PUT': ['ACCOUNTANT', 'MANAGER'],
        'PATCH': ['ACCOUNTANT', 'MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        return filter_by_query_params(
            super().get_queryset(), self.request,
            {'customer': 'customer_id', 'order': 'order_id'},
        )


class CustomerAccountViewSet(mixins.ListModelMixin,
                             mixins.RetrieveModelMixin,
                             viewsets.GenericViewSet):
    """What each customer owes, and the history behind it.

    Read-only: every figure is derived from orders and vouchers, so there is
    nothing here to write. Money moves by raising a voucher or approving an
    order.
    """

    serializer_class = CustomerAccountSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
    }

    def get_queryset(self):
        # Only customers the company has accepted: a pending request cannot
        # hold orders, so its row would be an unexplained line of zeroes.
        return customer_accounts().filter(status=Customer.Status.APPROVED)

    def _with_salesmen(self, customers):
        """One query for every row's salesman rather than one per row."""
        names = latest_salesman_names([customer.pk for customer in customers])
        for customer in customers:
            customer.salesman_name = names.get(customer.pk)
        return customers

    def list(self, request, *args, **kwargs):
        customers = self._with_salesmen(list(self.filter_queryset(self.get_queryset())))
        return Response(self.get_serializer(customers, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        customer = self.get_object()
        self._with_salesmen([customer])
        return Response(self.get_serializer(customer).data)

    @action(detail=True, methods=['get'])
    def statement(self, request, pk=None):
        """The account row plus what moved it: orders up, vouchers down."""
        customer = self.get_object()
        self._with_salesmen([customer])
        vouchers = Voucher.objects.filter(customer=customer).order_by('date', 'id')
        return Response({
            **self.get_serializer(customer).data,
            'orders': StatementOrderSerializer(billable_orders(customer), many=True).data,
            'vouchers': StatementVoucherSerializer(vouchers, many=True).data,
        })


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
