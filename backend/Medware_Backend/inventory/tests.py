from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from products.models import Product, ProductSupplier
from inventory.models import InventoryCategory, InventoryItem, SupplierBill, SupplierBillLine


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

    def test_manager_can_delete_category_by_detail_url(self):
        category = InventoryCategory.objects.create(name='Temporary')
        self.client.force_authenticate(user=self.manager)

        resp = self.client.delete(f'{self.list_url}{category.pk}/')

        self.assertEqual(resp.status_code, 204)
        self.assertFalse(InventoryCategory.objects.filter(pk=category.pk).exists())

    def test_product_is_imported_as_inventory_item(self):
        product = Product.objects.create(name='Gloves', whole_price='2.00', retail_price='3.00')

        item = InventoryItem.objects.get(product=product)

        self.assertEqual(item.name, product.name)
        self.assertEqual(item.quantity, 0)

    def test_supplier_bill_line_adds_quantity_to_inventory(self):
        product = Product.objects.create(name='Masks')
        item = InventoryItem.objects.get(product=product)
        supplier = ProductSupplier.objects.create(product=product)
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-08-28')

        SupplierBillLine.objects.create(bill=bill, item=item, quantity=25, category=item.category)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 25)

    def test_supplier_bill_line_updates_and_removes_quantity(self):
        product = Product.objects.create(name='Bandages')
        item = InventoryItem.objects.get(product=product)
        supplier = ProductSupplier.objects.create(product=product)
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-08-28')
        line = SupplierBillLine.objects.create(bill=bill, item=item, quantity=10, category=item.category)

        line.quantity = 4
        line.save()
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

        line.delete()
        item.refresh_from_db()
        self.assertEqual(item.quantity, 0)
