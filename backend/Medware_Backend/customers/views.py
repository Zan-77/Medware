from rest_framework import permissions, viewsets

from mysite.filters import filter_by_query_params
from users.permissions import RoleMethodPermission

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        # Salesmen read the list to pick a customer on the order form, but
        # customer records are entered by staff until the e-commerce slice.
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        return filter_by_query_params(super().get_queryset(), self.request, {'id': 'id'})
