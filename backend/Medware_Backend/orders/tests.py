from django.test import TestCase
from rest_framework.test import APIClient


class OrderAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/orders/order-requests/'

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests to order-requests should return 401"""
        resp = self.client.get(self.list_url)
        self.assertIn(resp.status_code, (401, 403))
