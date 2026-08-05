from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('manager', views.ManagerViewSet, basename='user-manager')
router.register('accountant', views.AccountantViewSet, basename='user-accountant')
router.register('salesman', views.SalesmanViewSet, basename='user-salesman')
router.register('customer', views.CustomerViewSet, basename='user-customer')

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/token/', views.CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', views.CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
]

urlpatterns += [
    path('users/me/', views.get_current_user, name='user-current'),
    path('users/roles/', views.get_available_roles, name='user-roles'),
    path('users/access/manager/', views.manager_access, name='user-manager-access'),
    path('users/access/accountant/', views.accountant_access, name='user-accountant-access'),
    path('users/access/salesman/', views.salesman_access, name='user-salesman-access'),
    path('users/access/customer/', views.customer_access, name='user-customer-access'),
    path('', include(router.urls)),
]
