from django.conf import settings
from django.http import JsonResponse
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .decorators import role_required
from .models import User
from .permissions import IsManager, IsAccountant, IsSalesman, IsCustomer
from .serializers import (
    CookieTokenRefreshSerializer,
    EmailOrUsernameTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)


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


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')
        if refresh_token:
            response.set_cookie(
                key='refresh',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )
        return response


class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data', {})
        if isinstance(data, dict):
            refresh_token = self.request.COOKIES.get('refresh')
            if refresh_token and 'refresh' not in data:
                data = {**data, 'refresh': refresh_token}
                kwargs['data'] = data
        return super().get_serializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')
        if refresh_token:
            response.set_cookie(
                key='refresh',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh', path='/')
        return response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = self.get_tokens_for_user(user)

        response_data = {
            'message': 'User registered successfully.',
            'user': UserSerializer(user).data,
        }
        response_data.update(tokens)

        response = Response(response_data, status=status.HTTP_201_CREATED)
        response.set_cookie(
            key='refresh',
            value=tokens['refresh'],
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            path='/',
        )
        return response

    def get_tokens_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


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
