from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView


from .decorators import role_required
from .models import User
from .permissions import IsManager, IsAccountant, IsSalesman, IsCustomer
from .serializers import UserSerializer, UserManagementSerializer, RegisterSerializer


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
        'features': [
            'Manage suppliers and supplier-category links',
            'Preview products, quantities, and inventory',
            'Create and edit bills and bill items',
            'Oversee accountant, salesman, and customer access',
            'Add, edit, and remove user roles',
        ],
    })


@role_required('ACCOUNTANT')
def accountant_access(request):
    return JsonResponse({
        'detail': 'Accountant access granted.',
        'role': request.user.role,
        'features': [
            'Review bills and purchase details',
            'Monitor supplier payment and costing information',
            'View product and inventory summaries',
        ],
    })


@role_required('SALESMAN')
def salesman_access(request):
    return JsonResponse({
        'detail': 'Salesman access granted.',
        'role': request.user.role,
        'features': [
            'View available products and categories',
            'Review inventory availability',
            'Work with product and supplier information',
        ],
    })


@role_required('CUSTOMER')
def customer_access(request):
    return JsonResponse({
        'detail': 'Customer access granted.',
        'role': request.user.role,
        'features': [
            'View accessible product information',
            'See relevant category and supplier details',
        ],
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


class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]
    http_method_names = ['get', 'patch', 'delete']

    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id).order_by('username')

    def partial_update(self, request, *args, **kwargs):
        if str(kwargs.get('pk')) == str(request.user.id):
            return Response(
                {'detail': 'Managers cannot change their own role through this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if str(kwargs.get('pk')) == str(request.user.id):
            return Response(
                {'detail': 'Managers cannot delete their own account through this endpoint.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create JWT tokens for the new user if SimpleJWT is available
        tokens = {}
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            tokens = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        except Exception:
            # SimpleJWT not installed or import failed; return user without tokens
            tokens = {}

        data = {'user': UserSerializer(user).data}
        data.update(tokens)
        return Response(data, status=status.HTTP_201_CREATED)
