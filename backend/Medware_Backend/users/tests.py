import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class UserRoleAccessTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.client = Client()
        self.manager = self.User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpass',
            role=self.User.Role.MANAGER,
            is_verified=True,
        )
        self.accountant = self.User.objects.create_user(
            username='accountant',
            email='accountant@example.com',
            password='accountantpass',
            role=self.User.Role.ACCOUNTANT,
            is_verified=True,
        )
        self.salesman = self.User.objects.create_user(
            username='salesman',
            email='salesman@example.com',
            password='salesmanpass',
            role=self.User.Role.SALESMAN,
            is_verified=True,
        )
        self.customer = self.User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customerpass',
            role=self.User.Role.CUSTOMER,
        )

    def test_unauthenticated_me_returns_401(self):
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, 401)

    def test_manager_endpoint(self):
        self.client.login(username='manager', password='managerpass')
        response = self.client.get('/api/users/access/manager/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], self.User.Role.MANAGER)

    def test_accountant_endpoint(self):
        self.client.login(username='accountant', password='accountantpass')
        response = self.client.get('/api/users/access/accountant/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], self.User.Role.ACCOUNTANT)

    def test_salesman_endpoint(self):
        self.client.login(username='salesman', password='salesmanpass')
        response = self.client.get('/api/users/access/salesman/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], self.User.Role.SALESMAN)

    def test_customer_endpoint(self):
        self.client.login(username='customer', password='customerpass')
        response = self.client.get('/api/users/access/customer/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], self.User.Role.CUSTOMER)

    def test_salesman_cannot_access_manager(self):
        self.client.login(username='salesman', password='salesmanpass')
        response = self.client.get('/api/users/access/manager/')
        self.assertEqual(response.status_code, 403)

    def test_login_by_email_sets_refresh_cookie(self):
        response = self.client.post(
            '/api/auth/token/',
            data=json.dumps({'email': 'manager@example.com', 'password': 'managerpass'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.cookies)
        self.assertTrue(response.cookies['refresh']['httponly'])

    def test_refresh_uses_refresh_cookie(self):
        login_response = self.client.post(
            '/api/auth/token/',
            data=json.dumps({'email': 'manager@example.com', 'password': 'managerpass'}),
            content_type='application/json',
        )
        self.assertEqual(login_response.status_code, 200)

        refresh_response = self.client.post('/api/auth/token/refresh/', content_type='application/json')
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn('access', refresh_response.json())

    def test_logout_clears_refresh_cookie(self):
        self.client.post(
            '/api/auth/token/',
            data=json.dumps({'email': 'manager@example.com', 'password': 'managerpass'}),
            content_type='application/json',
        )

        logout_response = self.client.post('/api/auth/logout/', content_type='application/json')
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.cookies['refresh']['max-age'], 0)

    def test_register_saves_first_and_last_name(self):
        response = self.client.post(
            '/api/auth/register/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'password': 'Newuserpass123!',
                'password2': 'Newuserpass123!',
                'role': self.User.Role.CUSTOMER,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        user = self.User.objects.get(username='newuser')
        self.assertEqual(user.first_name, 'Ada')
        self.assertEqual(user.last_name, 'Lovelace')
