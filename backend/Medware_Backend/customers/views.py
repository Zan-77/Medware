from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, status as http_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.response import Response

from audit.models import RequestTransition
from mysite.filters import filter_by_query_params
from notifications.models import Notification
from notifications.services import managers, notify, resolve
from users.permissions import RoleMethodPermission

from .models import Customer
from .serializers import CustomerSerializer

# Roles that see every customer regardless of who created it.
CUSTOMER_WIDE_ROLES = ('MANAGER', 'ACCOUNTANT')


class Conflict(APIException):
    """409 - the request is valid but the target is in the wrong state."""
    status_code = http_status.HTTP_409_CONFLICT
    default_detail = 'This record is in a state that does not allow the change.'


def _record_customer_transition(customer, from_status, actor, notes=''):
    RequestTransition.objects.create(
        source_model='Customer',
        source_id=str(customer.pk),
        from_status=from_status,
        to_status=customer.status,
        actor=actor,
        actor_role=getattr(actor, 'role', ''),
        notes=notes,
    )


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        # A salesman meets the customer; one who cannot add a customer cannot
        # raise an order. Theirs arrives as a request for a manager to approve.
        'POST': ['SALESMAN', 'MANAGER'],
        'PUT': ['SALESMAN', 'MANAGER'],
        'PATCH': ['SALESMAN', 'MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # Scope first, then filter: a query parameter must never widen what a
        # user can see.
        queryset = super().get_queryset().select_related('created_by')
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'role', '') in CUSTOMER_WIDE_ROLES):
            # A salesman sees approved customers plus their own unapproved
            # ones - never another salesman's pending record.
            queryset = queryset.filter(
                Q(status=Customer.Status.APPROVED) | Q(created_by=user))

        queryset = filter_by_query_params(queryset, self.request, {'id': 'id'})

        status_value = self.request.query_params.get('status')
        if status_value:
            if status_value not in Customer.Status.values:
                raise ValidationError({'status': f"'{status_value}' is not a valid status."})
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        is_manager = getattr(user, 'role', '') == 'MANAGER'
        with transaction.atomic():
            customer = serializer.save(
                created_by=user,
                status=Customer.Status.APPROVED if is_manager else Customer.Status.PENDING,
            )
            _record_customer_transition(customer, '', user)
            if not is_manager:
                notify(managers(), Notification.Kind.CUSTOMER_SUBMITTED, customer,
                       message=f'New customer {customer.name} awaiting approval.')

    def perform_update(self, serializer):
        # A salesman may correct their own request while it is still pending.
        # Anyone else's record, or one a manager has already decided on, is not
        # theirs to rewrite - editing after approval changes what was approved.
        customer = serializer.instance
        user = self.request.user
        if getattr(user, 'role', '') == 'SALESMAN':
            if customer.status != Customer.Status.PENDING:
                raise Conflict(
                    f'This customer is {customer.status} and can no longer be edited.')
            if customer.created_by_id != user.id:
                raise PermissionDenied('You may only edit customers you created.')
        serializer.save()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        # RoleMethodPermission checks the HTTP method, and POST is open to
        # SALESMAN on this viewset - so the role is checked here explicitly.
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may approve a customer.')

        with transaction.atomic():
            customer = Customer.objects.select_for_update().get(pk=self.get_object().pk)
            if customer.status != Customer.Status.PENDING:
                return Response(
                    {'detail': f'A customer in status {customer.status} cannot be approved.'},
                    status=http_status.HTTP_409_CONFLICT,
                )
            from_status = customer.status
            customer.status = Customer.Status.APPROVED
            customer.save(update_fields=['status'])
            _record_customer_transition(customer, from_status, request.user)
            # The manager's request row is answered; leaving it unread keeps
            # the badge counting a decision that has been made.
            resolve(Notification.Kind.CUSTOMER_SUBMITTED, customer)
            notify(
                [customer.created_by] if customer.created_by else [],
                Notification.Kind.CUSTOMER_APPROVED,
                customer,
                message=f'Customer {customer.name} was approved.',
            )
        return Response(self.get_serializer(customer).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may reject a customer.')

        notes = (request.data.get('notes') or '').strip()
        if not notes:
            raise ValidationError({'notes': 'A rejection reason is required.'})

        with transaction.atomic():
            customer = Customer.objects.select_for_update().get(pk=self.get_object().pk)
            if customer.status != Customer.Status.PENDING:
                return Response(
                    {'detail': f'A customer in status {customer.status} cannot be rejected.'},
                    status=http_status.HTTP_409_CONFLICT,
                )
            from_status = customer.status
            customer.status = Customer.Status.REJECTED
            customer.rejection_notes = notes
            customer.save(update_fields=['status', 'rejection_notes'])
            _record_customer_transition(customer, from_status, request.user, notes=notes)
            resolve(Notification.Kind.CUSTOMER_SUBMITTED, customer)
            notify(
                [customer.created_by] if customer.created_by else [],
                Notification.Kind.CUSTOMER_REJECTED,
                customer,
                message=f'Customer {customer.name} was rejected: {notes}',
            )
        return Response(self.get_serializer(customer).data)
