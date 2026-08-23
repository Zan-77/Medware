from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from inventory.models import InventoryCategory


class InventoryPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create users with different roles
        self.manager = User.objects.create_user(username='mgr', password='pass', role=User.Role.MANAGER)
        self.guest = User.objects.create_user(username='gst', password='pass', role=User.Role.GUEST)
        self.salesman = User.objects.create_user(username='slm', password='pass', role=User.Role.SALESMAN)
        self.warehouse = User.objects.create_user(username='wh', password='pass', role=User.Role.WAREHOUSE_WORKER)
        self.list_url = '/api/inventory/categories/'

    def test_manager_can_create_category(self):
        self.client.force_authenticate(user=self.manager)
        resp = self.client.post(self.list_url, {'name': 'Medicines'}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(InventoryCategory.objects.filter(name='Medicines').exists())

    def test_guest_cannot_create_category(self):
        self.client.force_authenticate(user=self.guest)
        resp = self.client.post(self.list_url, {'name': 'Supplies'}, format='json')
        self.assertIn(resp.status_code, (401, 403))

    def test_salesman_can_view_categories(self):
        # create category as manager
        InventoryCategory.objects.create(name='General')
        self.client.force_authenticate(user=self.salesman)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(len(data), 1)

    def test_warehouse_can_view_categories(self):
        InventoryCategory.objects.create(name='WarehouseCat')
        self.client.force_authenticate(user=self.warehouse)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
