from django.test import TestCase

# Create your tests here.
from rest_framework.test import APIClient

from users.models import User
from products.models import Product, ProductSupplier, Supplier


class ListFilterTests(TestCase):
    """Query parameters the frontend sends must actually narrow the list.

    `getSuppliersById` calls `/api/products/suppliers/?id=<id>` and
    `getProductSuppliersById` calls `/api/products/product-suppliers/?supplier=<id>`.
    DRF ignores query parameters a view was never told about, so both used to
    return the entire table.
    """

    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='prod_mgr', password='pass', role=User.Role.MANAGER)
        self.client.force_authenticate(user=self.manager)

        self.supplier_a = Supplier.objects.create(name='Alpha Supplies')
        self.supplier_b = Supplier.objects.create(name='Beta Supplies')
        self.product = Product.objects.create(name='Gloves')

        self.link_a = ProductSupplier.objects.create(product=self.product, supplier=self.supplier_a, discount=5)
        self.link_b = ProductSupplier.objects.create(product=self.product, supplier=self.supplier_b, discount=7)

    def test_suppliers_are_narrowed_to_the_requested_id(self):
        resp = self.client.get(f'/api/products/suppliers/?id={self.supplier_a.pk}')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.supplier_a.pk])

    def test_product_suppliers_are_narrowed_to_the_requested_supplier(self):
        resp = self.client.get(f'/api/products/product-suppliers/?supplier={self.supplier_b.pk}')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.link_b.pk])

    def test_a_non_numeric_id_is_rejected(self):
        resp = self.client.get('/api/products/suppliers/?id=not-a-number')

        self.assertEqual(resp.status_code, 400)
