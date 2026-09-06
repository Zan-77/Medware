from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from products.models import Product, Supplier
from inventory.models import InventoryCategory, InventoryItem, StockEntry, SupplierBill, SupplierBillLine


class InventoryPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create users with different roles
        self.manager = User.objects.create_user(username='mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.guest = User.objects.create_user(username='gst', password='pass', role=User.Role.GUEST)
        self.salesman = User.objects.create_user(username='slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.warehouse = User.objects.create_user(username='wh', password='pass', role=User.Role.WAREHOUSE_WORKER, is_verified=True)
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
        supplier = Supplier.objects.create(name='Acme Medical')
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-08-28')

        SupplierBillLine.objects.create(bill=bill, item=item, quantity=25, category=item.category)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 25)

    def test_supplier_bill_line_assigns_item_to_its_category(self):
        product = Product.objects.create(name='Gloves')
        item = InventoryItem.objects.get(product=product)
        supplier = Supplier.objects.create(name='Acme Medical')
        category = InventoryCategory.objects.create(name='Protective Equipment')
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-08-28')

        SupplierBillLine.objects.create(
            bill=bill,
            item=item,
            quantity=5,
            category=category,
        )

        item.refresh_from_db()
        self.assertEqual(item.category_id, category.pk)

    def test_inventory_item_exposes_supplier_bill_expiry_dates(self):
        product = Product.objects.create(name='Reagents')
        item = InventoryItem.objects.get(product=product)
        supplier = Supplier.objects.create(name='Acme Medical')
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-08-28')

        SupplierBillLine.objects.create(
            bill=bill,
            item=item,
            quantity=5,
            category=item.category,
            expiry_date='2027-01-15',
        )

        self.client.force_authenticate(user=self.manager)
        response = self.client.get(f'/api/inventory/items/?product={product.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['expiry_dates'], ['2027-01-15'])

    def test_supplier_bill_line_updates_and_removes_quantity(self):
        product = Product.objects.create(name='Bandages')
        item = InventoryItem.objects.get(product=product)
        supplier = Supplier.objects.create(name='Acme Medical')
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-08-28')
        line = SupplierBillLine.objects.create(bill=bill, item=item, quantity=10, category=item.category)

        line.quantity = 4
        line.save()
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

        line.delete()
        item.refresh_from_db()
        self.assertEqual(item.quantity, 0)


class ListFilterTests(TestCase):
    """Query parameters the frontend sends must actually narrow the list.

    The frontend asks for one bill's lines with
    `/api/inventory/bill-lines/?bill=<id>`. DRF ignores query parameters a
    view was never told about, so before these filters existed that request
    returned every line of every bill - the "ask for one bill, get every id
    back" bug. Each test here pins one of those parameters.
    """

    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='filter_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.client.force_authenticate(user=self.manager)

        self.supplier_a = Supplier.objects.create(name='Alpha Supplies')
        self.supplier_b = Supplier.objects.create(name='Beta Supplies')

        self.category_a = InventoryCategory.objects.create(name='Syringes')
        self.category_b = InventoryCategory.objects.create(name='Dressings')

        self.item_a = InventoryItem.objects.create(name='Syringe 5ml', category=self.category_a)
        self.item_b = InventoryItem.objects.create(name='Gauze roll', category=self.category_b)

        self.bill_a = SupplierBill.objects.create(supplier=self.supplier_a, manager=self.manager, date='2026-09-01')
        self.bill_b = SupplierBill.objects.create(supplier=self.supplier_b, manager=self.manager, date='2026-09-02')

        self.line_a = SupplierBillLine.objects.create(bill=self.bill_a, item=self.item_a, category=self.category_a, quantity=5)
        self.line_b = SupplierBillLine.objects.create(bill=self.bill_b, item=self.item_b, category=self.category_b, quantity=7)

    def test_bill_lines_are_narrowed_to_the_requested_bill(self):
        resp = self.client.get(f'/api/inventory/bill-lines/?bill={self.bill_a.pk}')

        self.assertEqual(resp.status_code, 200)
        ids = [row['id'] for row in resp.json()]
        self.assertEqual(ids, [self.line_a.pk])

    def test_bill_lines_are_narrowed_to_the_requested_supplier(self):
        resp = self.client.get(f'/api/inventory/bill-lines/?supplier={self.supplier_b.pk}')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.line_b.pk])

    def test_bill_lines_without_a_filter_still_return_everything(self):
        resp = self.client.get('/api/inventory/bill-lines/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)

    def test_bill_lines_reject_a_non_numeric_bill_id(self):
        """A typo must fail loudly, not silently widen the result set."""
        resp = self.client.get('/api/inventory/bill-lines/?bill=not-a-number')

        self.assertEqual(resp.status_code, 400)

    def test_bill_lines_are_narrowed_to_the_requested_item(self):
        resp = self.client.get(f'/api/inventory/bill-lines/?item={self.item_b.pk}')

        self.assertEqual([row['id'] for row in resp.json()], [self.line_b.pk])

    def test_bills_are_narrowed_to_the_requested_supplier(self):
        resp = self.client.get(f'/api/inventory/bills/?supplier={self.supplier_b.pk}')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.bill_b.pk])

    def test_items_are_narrowed_to_the_requested_category(self):
        resp = self.client.get(f'/api/inventory/items/?category={self.category_a.pk}')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.item_a.pk])

    def test_stock_entries_are_narrowed_to_the_requested_item(self):
        entry = StockEntry.objects.create(item=self.item_a, quantity=3)
        StockEntry.objects.create(item=self.item_b, quantity=4)

        resp = self.client.get(f'/api/inventory/stock-entries/?item={self.item_a.pk}')

        self.assertEqual(resp.status_code, 200)
        returned = {row['id'] for row in resp.json()}
        self.assertIn(entry.pk, returned)
        self.assertTrue(all(row['item'] == self.item_a.pk for row in resp.json()))


class ReadableNameFieldTests(TestCase):
    """Bill rows carry the names the tables display.

    `ProductSupplierSerializer` already exposes `product_name`/`supplier_name`;
    the inventory serializers follow that pattern so a table does not have to
    issue one request per row to turn an id into a label.
    """

    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='name_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.client.force_authenticate(user=self.manager)

        self.supplier = Supplier.objects.create(name='Alpha Supplies')
        self.category = InventoryCategory.objects.create(name='Syringes')
        self.item = InventoryItem.objects.create(name='Syringe 5ml', category=self.category)
        self.bill = SupplierBill.objects.create(supplier=self.supplier, manager=self.manager, date='2026-09-01')
        self.line = SupplierBillLine.objects.create(bill=self.bill, item=self.item, category=self.category, quantity=5)

    def test_bill_carries_its_supplier_name(self):
        row = self.client.get(f'/api/inventory/bills/{self.bill.pk}/').json()

        self.assertEqual(row['supplier_name'], 'Alpha Supplies')

    def test_bill_line_carries_item_and_category_names(self):
        row = self.client.get(f'/api/inventory/bill-lines/{self.line.pk}/').json()

        self.assertEqual(row['item_name'], 'Syringe 5ml')
        self.assertEqual(row['category_name'], 'Syringes')

    def test_a_line_whose_item_was_deleted_still_serialises(self):
        """`item` is nullable (SET_NULL), so the name must tolerate a null FK."""
        self.item.delete()
        self.line.refresh_from_db()

        row = self.client.get(f'/api/inventory/bill-lines/{self.line.pk}/').json()

        self.assertIsNone(row['item'])
        self.assertIsNone(row['item_name'])


class DecimalRepresentationTests(TestCase):
    """Money comes back as JSON numbers, not strings.

    DRF's default (`COERCE_DECIMAL_TO_STRING`) renders every DecimalField as
    a quoted string. The frontend types declare `unit_price`/`discount`/
    `whole_price` as numbers and feeds them to numeric range filters, so a
    string silently broke sorting and filtering on those columns.
    """

    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='dec_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.client.force_authenticate(user=self.manager)

        supplier = Supplier.objects.create(name='Alpha Supplies')
        category = InventoryCategory.objects.create(name='Syringes')
        item = InventoryItem.objects.create(name='Syringe 5ml', category=category)
        bill = SupplierBill.objects.create(supplier=supplier, manager=self.manager, date='2026-09-01')
        self.line = SupplierBillLine.objects.create(
            bill=bill, item=item, category=category, quantity=5,
            unit_price='12.50', discount='1.25',
        )

    def test_bill_line_money_fields_are_numbers(self):
        row = self.client.get(f'/api/inventory/bill-lines/{self.line.pk}/').json()

        self.assertIsInstance(row['unit_price'], float)
        self.assertEqual(row['unit_price'], 12.5)
        self.assertIsInstance(row['discount'], float)
