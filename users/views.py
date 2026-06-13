from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .decorators import role_required
from .models import User
from .permissions import IsManager, IsAccountant, IsSalesman, IsCustomer
from .serializers import UserSerializer


def get_current_user(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Authentication required.'}, status=401)

    return JsonResponse({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'role': request.user.role,
        'role_display': request.user.get_role_display(),
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
    })


def get_available_roles(request):
    return JsonResponse({
        'roles': [
            {'key': key, 'label': label}
            for key, label in User.Role.choices
        ]
    })


@role_required('MANAGER')
def manager_access(request):
    return JsonResponse({
        'detail': 'Manager/Admin access granted.',
        'role': request.user.role,
    })


@role_required('ACCOUNTANT')
def accountant_access(request):
    return JsonResponse({
        'detail': 'Accountant access granted.',
        'role': request.user.role,
    })


@role_required('SALESMAN')
def salesman_access(request):
    return JsonResponse({
        'detail': 'Salesman access granted.',
        'role': request.user.role,
    })


@role_required('CUSTOMER')
def customer_access(request):
    return JsonResponse({
        'detail': 'Customer access granted.',
        'role': request.user.role,
    })


class RoleBaseViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def list(self, request):
        serializer = self.serializer_class(request.user)
        return Response({
            'message': self.permission_message,
            'user': serializer.data,
        })


class ManagerViewSet(RoleBaseViewSet):
    permission_classes = [permissions.IsAuthenticated, IsManager]
    permission_message = 'Manager/Admin access granted via DRF.'


class AccountantViewSet(RoleBaseViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAccountant]
    permission_message = 'Accountant access granted via DRF.'


class SalesmanViewSet(RoleBaseViewSet):
    permission_classes = [permissions.IsAuthenticated, IsSalesman]
    permission_message = 'Salesman access granted via DRF.'


class CustomerViewSet(RoleBaseViewSet):
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    permission_message = 'Customer access granted via DRF.'
