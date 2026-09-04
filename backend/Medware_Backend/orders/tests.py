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


from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from orders.models import OrderItem, OrderRequest
from products.models import Product
from users.models import User


class OrderStatusFieldTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='st_slm', password='pass', role=User.Role.SALESMAN)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')
        self.order = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman)

    def test_a_new_order_starts_pending(self):
        self.assertEqual(self.order.status, OrderRequest.Status.PENDING)

    def test_order_total_is_the_sum_of_its_lines(self):
        OrderItem.objects.create(order_request=self.order, product=self.product,
                                 quantity=3, sell_price=Decimal('10.50'))
        OrderItem.objects.create(order_request=self.order, product=self.product,
                                 quantity=2, sell_price=Decimal('4.00'))

        self.assertEqual(self.order.total, Decimal('39.50'))

    def test_line_total_is_quantity_times_price(self):
        item = OrderItem.objects.create(order_request=self.order, product=self.product,
                                        quantity=4, sell_price=Decimal('2.25'))

        self.assertEqual(item.line_total, Decimal('9.00'))

    def test_salesman_cannot_patch_their_order_to_approved(self):
        """The regression test for the original hole: `status` was a writable
        free-text field, so a salesman could approve their own order."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/orders/order-requests/{self.order.pk}/',
                                 {'status': 'APPROVED'}, format='json')

        self.order.refresh_from_db()
        self.assertIn(resp.status_code, (200, 400))
        self.assertEqual(self.order.status, OrderRequest.Status.PENDING)

    def test_order_detail_carries_readable_names_and_total(self):
        OrderItem.objects.create(order_request=self.order, product=self.product,
                                 quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.salesman)

        row = self.client.get(f'/api/orders/order-requests/{self.order.pk}/').json()

        self.assertEqual(row['customer_name'], 'Al Noor Pharmacy')
        self.assertEqual(row['salesman_name'], 'st_slm')
        self.assertEqual(Decimal(str(row['total'])), Decimal('20.00'))
