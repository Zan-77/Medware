from rest_framework import viewsets, permissions
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


def scope_to_user(queryset, user, customer_field='customer', salesman_field='salesman'):
    """Narrow `queryset` to rows the given user is a party to."""
    if user.is_superuser or getattr(user, 'role', None) in ORDER_WIDE_ROLES:
        return queryset
    if getattr(user, 'role', None) == 'SALESMAN':
        return queryset.filter(**{salesman_field: user})
    return queryset.filter(**{customer_field: user})


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


class OrderReviewViewSet(viewsets.ModelViewSet):
    queryset = OrderReview.objects.all()
    serializer_class = OrderReviewSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['MANAGER'],
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
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
