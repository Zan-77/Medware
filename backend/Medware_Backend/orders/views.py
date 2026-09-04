from decimal import Decimal

from django.db import transaction
from rest_framework import mixins, permissions, viewsets
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import RequestTransition
from notifications.models import Notification
from notifications.services import managers, notify

from .models import OrderRequest, OrderItem, OrderReview, OrderFinalization, PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval
from .serializers import (
    OrderRequestSerializer, OrderItemSerializer, OrderReviewSerializer,
    OrderFinalizationSerializer, PackagingTaskSerializer, ReturnRequestSerializer,
    ReturnAssessmentSerializer, ReturnApprovalSerializer
)
from users.permissions import RoleMethodPermission

# Roles that legitimately see every order in the system. Everyone else is
# narrowed to the rows they are a party to, so one customer can never read
# or modify another customer's order.
ORDER_WIDE_ROLES = ('MANAGER', 'ACCOUNTANT', 'WAREHOUSE_WORKER')


class Conflict(APIException):
    """409 - the request is valid but the target is in the wrong state."""
    status_code = http_status.HTTP_409_CONFLICT
    default_detail = 'This record is in a state that does not allow the change.'


def scope_to_user(queryset, user, customer_field='customer', salesman_field='salesman'):
    """Narrow `queryset` to rows the given user is a party to."""
    if user.is_superuser or getattr(user, 'role', None) in ORDER_WIDE_ROLES:
        return queryset
    if getattr(user, 'role', None) == 'SALESMAN':
        return queryset.filter(**{salesman_field: user})
    return queryset.filter(**{customer_field: user})


def _record_transition(order, from_status, actor, notes=''):
    RequestTransition.objects.create(
        source_model='OrderRequest',
        source_id=str(order.pk),
        from_status=from_status,
        to_status=order.status,
        actor=actor,
        actor_role=getattr(actor, 'role', ''),
        notes=notes,
    )


def _approve(order, manager):
    """Flip to APPROVED, freezing the balances the customer agreed to.

    Reads finance.CustomerBalance but never writes it - moving the real
    balance is the accountant's finalize step, which is a later slice.
    """
    from finance.models import CustomerBalance

    from_status = order.status
    balance = CustomerBalance.objects.filter(customer=order.customer).first()
    order.previous_balance = balance.outstanding_balance if balance else Decimal('0')
    order.new_balance = order.previous_balance + order.total
    order.status = OrderRequest.Status.APPROVED
    order.save(update_fields=['status', 'previous_balance', 'new_balance'])

    OrderReview.objects.create(order=order, manager=manager, decision='APPROVE', notes='')
    _record_transition(order, from_status, manager)
    notify(
        [order.salesman] if order.salesman else [],
        Notification.Kind.ORDER_APPROVED,
        order,
        message=f'Order {order.pk} was approved.',
    )


class OrderRequestViewSet(viewsets.ModelViewSet):
    queryset = OrderRequest.objects.all()
    serializer_class = OrderRequestSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    # POST: create request (Salesman, Manager, Customer)
    # GET: list/retrieve (Manager, Accountant, Salesman, Warehouse Worker, Customer)
    # PATCH/PUT: modification requests allowed pre-shipment (Customer, Salesman, Manager, Accountant)
    allowed_roles_by_method = {
        'POST': ['SALESMAN', 'MANAGER', 'CUSTOMER'],
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER'],
        'PUT': ['CUSTOMER', 'SALESMAN', 'MANAGER', 'ACCOUNTANT'],
        'PATCH': ['CUSTOMER', 'SALESMAN', 'MANAGER', 'ACCOUNTANT'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # OrderRequest.customer is now a Customer record; the path to the
        # account that may read it is customer__user. ReturnRequest still
        # points straight at User, which is why this is set per call site
        # rather than changed in scope_to_user itself.
        return scope_to_user(super().get_queryset(), self.request.user,
                             customer_field='customer__user')

    def perform_create(self, serializer):
        """`origin` and `salesman` come from the requesting user, never the
        client. A manager's own order is approved in the same transaction, so
        every order reaching the accountant has exactly one review row."""
        user = self.request.user
        role = getattr(user, 'role', '')
        with transaction.atomic():
            order = serializer.save(
                origin=role if role in ('SALESMAN', 'MANAGER', 'CUSTOMER') else 'SALESMAN',
                salesman=user if role == 'SALESMAN' else None,
            )
            if role == 'MANAGER':
                _approve(order, user)
            else:
                notify(managers(), Notification.Kind.ORDER_SUBMITTED, order,
                       message=f'New order {order.pk} awaiting review.')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        # RoleMethodPermission checks the HTTP method, and POST is open to
        # SALESMAN on this viewset - so the role is checked here explicitly.
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may approve an order.')

        with transaction.atomic():
            # Lock the row and re-check inside the transaction: without this,
            # two concurrent approvals both pass the status check and each
            # writes a review, an audit row and a notification.
            order = OrderRequest.objects.select_for_update().get(pk=self.get_object().pk)
            if order.status != OrderRequest.Status.PENDING:
                return Response(
                    {'detail': f'An order in status {order.status} cannot be approved.'},
                    status=http_status.HTTP_409_CONFLICT,
                )
            _approve(order, request.user)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may reject an order.')

        notes = (request.data.get('notes') or '').strip()
        if not notes:
            raise ValidationError({'notes': 'A rejection reason is required.'})

        with transaction.atomic():
            # Lock the row and re-check inside the transaction: without this,
            # two concurrent approvals both pass the status check and each
            # writes a review, an audit row and a notification.
            order = OrderRequest.objects.select_for_update().get(pk=self.get_object().pk)
            if order.status != OrderRequest.Status.PENDING:
                return Response(
                    {'detail': f'An order in status {order.status} cannot be rejected.'},
                    status=http_status.HTTP_409_CONFLICT,
                )
            from_status = order.status
            order.status = OrderRequest.Status.REJECTED
            order.save(update_fields=['status'])
            OrderReview.objects.create(order=order, manager=request.user,
                                       decision='DECLINE', notes=notes)
            _record_transition(order, from_status, request.user, notes=notes)
            notify(
                [order.salesman] if order.salesman else [],
                Notification.Kind.ORDER_REJECTED,
                order,
                message=f'Order {order.pk} was rejected: {notes}',
            )
        return Response(self.get_serializer(order).data)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER'],
        'POST': ['MANAGER', 'ACCOUNTANT'],
        'PUT': ['MANAGER', 'ACCOUNTANT'],
        'PATCH': ['MANAGER', 'ACCOUNTANT'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # Items are scoped through their parent order request.
        return scope_to_user(
            super().get_queryset(),
            self.request.user,
            customer_field='order_request__customer__user',
            salesman_field='order_request__salesman',
        )

    def _assert_parent_pending(self, order):
        if order.status != OrderRequest.Status.PENDING:
            raise Conflict(f'Order {order.pk} is {order.status} and its items are frozen.')

    def perform_create(self, serializer):
        # `order_request` is optional on the serializer so the parent can supply
        # it during nested creation. On a direct POST it is required - without
        # this it raised a bare KeyError and DRF returned 500.
        order = serializer.validated_data.get('order_request')
        if order is None:
            raise ValidationError({'order_request': 'This field is required.'})
        self._assert_parent_pending(order)
        serializer.save()

    def perform_update(self, serializer):
        self._assert_parent_pending(serializer.instance.order_request)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_parent_pending(instance.order_request)
        instance.delete()


class OrderReviewViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only: reviews are written by the approve/reject actions, never
    posted directly - a hand-written review walks around the state machine."""

    queryset = OrderReview.objects.all()
    serializer_class = OrderReviewSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
    }


class OrderFinalizationViewSet(viewsets.ModelViewSet):
    queryset = OrderFinalization.objects.all()
    serializer_class = OrderFinalizationSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['ACCOUNTANT'],
        'GET': ['ACCOUNTANT', 'MANAGER'],
        'PUT': ['ACCOUNTANT'],
        'PATCH': ['ACCOUNTANT'],
        'DELETE': ['MANAGER'],
    }


class PackagingTaskViewSet(viewsets.ModelViewSet):
    queryset = PackagingTask.objects.all()
    serializer_class = PackagingTaskSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['WAREHOUSE_WORKER'],
        'GET': ['WAREHOUSE_WORKER', 'MANAGER', 'ACCOUNTANT'],
        'PUT': ['WAREHOUSE_WORKER'],
        'PATCH': ['WAREHOUSE_WORKER'],
        'DELETE': ['MANAGER'],
    }


class ReturnRequestViewSet(viewsets.ModelViewSet):
    queryset = ReturnRequest.objects.all()
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['CUSTOMER', 'SALESMAN'],
        'GET': ['MANAGER', 'ACCOUNTANT', 'WAREHOUSE_WORKER', 'SALESMAN', 'CUSTOMER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        return scope_to_user(super().get_queryset(), self.request.user)


class ReturnAssessmentViewSet(viewsets.ModelViewSet):
    queryset = ReturnAssessment.objects.all()
    serializer_class = ReturnAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['WAREHOUSE_WORKER'],
        'GET': ['MANAGER', 'WAREHOUSE_WORKER', 'ACCOUNTANT'],
        'PUT': ['WAREHOUSE_WORKER'],
        'PATCH': ['WAREHOUSE_WORKER'],
        'DELETE': ['MANAGER'],
    }


class ReturnApprovalViewSet(viewsets.ModelViewSet):
    queryset = ReturnApproval.objects.all()
    serializer_class = ReturnApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['MANAGER'],
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }


class InboxView(APIView):
    """What is waiting for the requesting user.

    For the queue roles this derives from order status, so it cannot drift:
    an order is in the manager's queue because it *is* pending, not because a
    row somewhere says so. The salesman's rows are events rather than work,
    so they come from unread notifications.
    """

    permission_classes = [permissions.IsAuthenticated]

    QUEUE_STATUS_BY_ROLE = {
        'MANAGER': OrderRequest.Status.PENDING,
        'ACCOUNTANT': OrderRequest.Status.APPROVED,
        # Empty until the finance slice introduces FINALIZED orders.
        'WAREHOUSE_WORKER': OrderRequest.Status.FINALIZED,
    }

    def get(self, request):
        role = getattr(request.user, 'role', '')
        if role not in list(self.QUEUE_STATUS_BY_ROLE) + ['SALESMAN']:
            raise PermissionDenied('This role has no request inbox.')

        if role == 'SALESMAN':
            items = self._salesman_updates(request)
        else:
            items = self._queue(request, self.QUEUE_STATUS_BY_ROLE[role])

        return Response({'role': role, 'count': len(items), 'items': items})

    def _queue(self, request, status_value):
        orders = OrderRequest.objects.filter(status=status_value).order_by('created_at')
        return [
            {
                'kind': f'ORDER_{status_value}',
                'order': OrderRequestSerializer(order, context={'request': request}).data,
                'message': '',
                'notification_id': None,
            }
            for order in orders
        ]

    def _salesman_updates(self, request):
        unread = Notification.objects.filter(
            recipient=request.user,
            kind=Notification.Kind.ORDER_REJECTED,
            read_at__isnull=True,
        )
        items = []
        for notification in unread:
            # `target_id` is a CharField and the model is documented as taking
            # non-order targets in future, so a value that is not an order pk
            # must skip this row rather than 500 the whole inbox.
            try:
                target_pk = int(notification.target_id)
            except (TypeError, ValueError):
                continue
            order = OrderRequest.objects.filter(pk=target_pk).first()
            if order is None:
                continue
            items.append({
                'kind': 'ORDER_REJECTED',
                'order': OrderRequestSerializer(order, context={'request': request}).data,
                'message': notification.message,
                'notification_id': notification.pk,
            })
        return items
