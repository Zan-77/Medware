from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class UserRoleAccessTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.client = Client()
        self.manager = self.User.objects.create_user(
            username='manager', password='managerpass', role=self.User.Role.MANAGER
        )
        self.accountant = self.User.objects.create_user(
            username='accountant', password='accountantpass', role=self.User.Role.ACCOUNTANT
        )
        self.salesman = self.User.objects.create_user(
            username='salesman', password='salesmanpass', role=self.User.Role.SALESMAN
        )
        self.customer = self.User.objects.create_user(
            username='customer', password='customerpass', role=self.User.Role.CUSTOMER
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
