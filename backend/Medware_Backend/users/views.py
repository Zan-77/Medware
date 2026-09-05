from django.conf import settings
from django.http import JsonResponse
from rest_framework import mixins, status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from audit.models import RequestTransition

from .decorators import role_required
from .models import User
from .permissions import IsManager, IsAccountant, IsSalesman, IsCustomer
from .serializers import (
    CookieTokenRefreshSerializer,
    EmailOrUsernameTokenObtainPairSerializer,
    RegisterSerializer,
    UserAdminSerializer,
    UserSerializer,
    build_tokens_for_user,
)


# Must be a DRF view: as a plain Django view this only ever saw Django's
# session auth and returned 401 for every JWT-authenticated caller, which is
# how the SPA talks to the API.
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    return Response(UserSerializer(request.user).data)


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get('refresh')
        access_token = response.data.get('access')
        status_code = getattr(response, 'status_code', 200)

        if refresh_token:
            # store refresh token in a secure httpOnly cookie
            # and return only the access token in the response body
            resp = Response({'access': access_token}, status=status_code)
            resp.set_cookie(
                key='refresh',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )
            return resp

        # fallback: no refresh present, return whatever the superclass returned
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
        access_token = response.data.get('access')
        status_code = getattr(response, 'status_code', 200)

        if refresh_token:
            resp = Response({'access': access_token}, status=status_code)
            resp.set_cookie(
                key='refresh',
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )
            return resp

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
        # context carries the request so the serializer can tell whether the
        # caller is a manager granting a staff role vs. an anonymous signup.
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = build_tokens_for_user(user)

        response_data = {
            'access': tokens["access"],
        }
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


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_roles(request):
    return Response({
        'roles': [
            {'key': key, 'label': label}
            for key, label in User.Role.choices
        ]
    })


# These are DRF views rather than plain Django views for the same reason as
# get_current_user: the `role_required` decorator only understands session
# auth, so JWT callers were rejected with 401 before the role was ever read.
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsManager])
def manager_access(request):
    return Response({
        'detail': 'Manager/Admin access granted.',
        'role': request.user.role,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAccountant])
def accountant_access(request):
    return Response({
        'detail': 'Accountant access granted.',
        'role': request.user.role,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesman])
def salesman_access(request):
    return Response({
        'detail': 'Salesman access granted.',
        'role': request.user.role,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomer])
def customer_access(request):
    return Response({
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


class UserAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Manager-only account administration: grant a role, approve an account.

    No create and no destroy - accounts are made by registering, and deleting
    one would cascade into the orders and customers that reference it.
    """

    queryset = User.objects.all().order_by('username')
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def perform_update(self, serializer):
        target = serializer.instance
        actor = self.request.user

        # Both guards exist to stop one careless click locking the company out.
        if target.pk == actor.pk:
            raise PermissionDenied(
                'You cannot change your own role or verification.')
        if target.is_superuser:
            raise PermissionDenied('A superuser account cannot be changed here.')

        before_role, before_verified = target.role, target.is_verified
        user = serializer.save()

        if user.role == before_role and user.is_verified == before_verified:
            return

        changes = []
        if user.role != before_role:
            changes.append(f'role: {before_role} -> {user.role}')
        if user.is_verified != before_verified:
            changes.append(f'verified: {before_verified} -> {user.is_verified}')

        RequestTransition.objects.create(
            source_model='User',
            source_id=str(user.pk),
            from_status=f'role={before_role},verified={before_verified}',
            to_status=f'role={user.role},verified={user.is_verified}',
            actor=actor,
            actor_role=getattr(actor, 'role', ''),
            notes='; '.join(changes),
        )
