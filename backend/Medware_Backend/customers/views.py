from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from audit.models import RequestTransition
from mysite.filters import filter_by_query_params
from notifications.models import Notification
from notifications.services import managers, notify
from users.permissions import RoleMethodPermission

from .models import Customer
from .serializers import CustomerSerializer

# Roles that see every customer regardless of who created it.
CUSTOMER_WIDE_ROLES = ('MANAGER', 'ACCOUNTANT')


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
