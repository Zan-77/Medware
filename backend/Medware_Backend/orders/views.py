from rest_framework import viewsets, permissions
from .models import OrderRequest, OrderItem, OrderReview, OrderFinalization, PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval
from .serializers import (
    OrderRequestSerializer, OrderItemSerializer, OrderReviewSerializer,
    OrderFinalizationSerializer, PackagingTaskSerializer, ReturnRequestSerializer,
    ReturnAssessmentSerializer, ReturnApprovalSerializer
)
from users.permissions import RoleMethodPermission


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


class OrderReviewViewSet(viewsets.ModelViewSet):
    queryset = OrderReview.objects.all()
    serializer_class = OrderReviewSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['MANAGER'],
        'GET': ['MANAGER', 'ACCOUNTANT'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
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
    }


class ReturnAssessmentViewSet(viewsets.ModelViewSet):
    queryset = ReturnAssessment.objects.all()
    serializer_class = ReturnAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'POST': ['WAREHOUSE_WORKER'],
        'GET': ['MANAGER', 'WAREHOUSE_WORKER', 'ACCOUNTANT'],
        'PUT': ['WAREHOUSE_WORKER'],
        'PATCH': ['WAREHOUSE_WORKER'],
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
    }
