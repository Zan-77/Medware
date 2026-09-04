"""API method matrix.

Exercises every HTTP method against every registered endpoint, on both the
list URL and the detail URL, as an authorised role. Run with:

    python manage.py test scripts.method_matrix --verbosity 1

Reading the output:
    2xx  routed, permitted, accepted
    400  routed and permitted - only the sample payload was rejected
    403  routed, but this role is not allowed the method
    405  NOT ROUTED - the method does not exist at that URL shape
    404  no such URL

405 is the one that matters for the "method not allowed" reports: DRF routers
map list URLs (/thing/) to GET+POST only, and detail URLs (/thing/1/) to
GET+PUT+PATCH+DELETE only. A DELETE to a list URL, or a POST to a detail URL,
is a 405 by design and is not a bug.
"""

from django.db import transaction
from django.test import TestCase
from rest_framework.test import APIClient

from users.models import User
from products.models import Product, Supplier, ProductSupplier
from inventory.models import InventoryCategory, InventoryItem, SupplierBill, SupplierBillLine, StockEntry
from orders.models import (
    OrderRequest, OrderItem, OrderReview, OrderFinalization,
    PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval,
)
from finance.models import Voucher, PaymentRecord, CommissionRecord, CustomerBalance
from audit.models import AuditLog, RequestTransition
from website.models import WebsiteCustomerProfile, WebsiteCatalog, WebsiteCatalogItem

METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']


class MethodMatrixTest(TestCase):
    maxDiff = None

    def setUp(self):
        self.client = APIClient()
        self.users = {
            role: User.objects.create_user(
                username=f'mm_{role.lower()}',
                email=f'mm_{role.lower()}@example.com',
                password='pass1234',
                role=role,
            )
            for role in ['MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER', 'CUSTOMER', 'GUEST']
        }

        # --- seed one row per resource so detail URLs exist -----------------
        self.supplier = Supplier.objects.create(name='Acme', phone='123')
        self.product = Product.objects.create(name='Widget', whole_price='1.00', retail_price='2.00')
        self.prodsup = ProductSupplier.objects.create(product=self.product, supplier=self.supplier, discount='5.00')

        self.item = InventoryItem.objects.get(product=self.product)
        self.category = self.item.category
        self.bill = SupplierBill.objects.create(supplier=self.supplier, manager=self.users['MANAGER'], date='2026-08-28')
        self.billline = SupplierBillLine.objects.create(bill=self.bill, item=self.item, quantity=5, category=self.category)
        self.stock = StockEntry.objects.filter(item=self.item).first() or \
            StockEntry.objects.create(item=self.item, quantity=1)

        from customers.models import Customer
        self.customer_record = Customer.objects.create(name='Matrix customer', user=self.users['CUSTOMER'])
        self.order = OrderRequest.objects.create(
            origin='CUSTOMER', customer=self.customer_record, salesman=self.users['SALESMAN'], status='PENDING')
        self.orderitem = OrderItem.objects.create(
            order_request=self.order, product=self.product, quantity=1, sell_price='2.00')
        self.review = OrderReview.objects.create(order=self.order, manager=self.users['MANAGER'], decision='APPROVE')
        self.finalization = OrderFinalization.objects.create(order=self.order, accountant=self.users['ACCOUNTANT'])
        self.packaging = PackagingTask.objects.create(order=self.order, warehouse_worker=self.users['WAREHOUSE_WORKER'])
        self.retreq = ReturnRequest.objects.create(
            order=self.order, customer=self.users['CUSTOMER'], salesman=self.users['SALESMAN'], reason='damaged')
        self.retassess = ReturnAssessment.objects.create(
            return_request=self.retreq, warehouse_worker=self.users['WAREHOUSE_WORKER'])
        self.retappr = ReturnApproval.objects.create(
            return_request=self.retreq, manager=self.users['MANAGER'], approved=True)

        self.voucher = Voucher.objects.create(order=self.order, salesman=self.users['SALESMAN'], amount='10.00')
        self.payment = PaymentRecord.objects.create(
            order=self.order, customer=self.users['CUSTOMER'], amount='10.00', recorded_by=self.users['ACCOUNTANT'])
        self.commission = CommissionRecord.objects.create(
            order=self.order, salesman=self.users['SALESMAN'], percentage='5.00', earned_amount='1.00')
        self.balance = CustomerBalance.objects.create(customer=self.customer_record)

        self.auditlog = AuditLog.objects.create(user=self.users['MANAGER'], action='seed')
        self.transition = RequestTransition.objects.create(
            source_model='OrderRequest', source_id='1', from_status='A', to_status='B')

        self.profile = WebsiteCustomerProfile.objects.create(user=self.users['CUSTOMER'])
        self.catalog = WebsiteCatalog.objects.create(title='Main')
        self.catalogitem = WebsiteCatalogItem.objects.create(catalog=self.catalog, name='Thing')

        # endpoint -> (list url, detail pk, role allowed to write)
        self.endpoints = [
            ('products/suppliers',        '/api/products/suppliers/',          self.supplier.pk,    'MANAGER'),
            ('products/products',         '/api/products/products/',           self.product.pk,     'MANAGER'),
            ('products/product-suppliers', '/api/products/product-suppliers/', self.prodsup.pk,     'MANAGER'),

            ('inventory/categories',      '/api/inventory/categories/',        self.category.pk,    'MANAGER'),
            ('inventory/items',           '/api/inventory/items/',             self.item.pk,        'MANAGER'),
            ('inventory/bills',           '/api/inventory/bills/',             self.bill.pk,        'MANAGER'),
            ('inventory/bill-lines',      '/api/inventory/bill-lines/',        self.billline.pk,    'MANAGER'),
            ('inventory/stock-entries',   '/api/inventory/stock-entries/',     self.stock.pk,       'MANAGER'),

            ('orders/order-requests',     '/api/orders/order-requests/',       self.order.pk,       'MANAGER'),
            ('orders/order-items',        '/api/orders/order-items/',          self.orderitem.pk,   'MANAGER'),
            ('orders/reviews',            '/api/orders/reviews/',              self.review.pk,      'MANAGER'),
            ('orders/finalizations',      '/api/orders/finalizations/',        self.finalization.pk, 'ACCOUNTANT'),
            ('orders/packaging',          '/api/orders/packaging/',            self.packaging.pk,   'WAREHOUSE_WORKER'),
            ('orders/return-requests',    '/api/orders/return-requests/',      self.retreq.pk,      'MANAGER'),
            ('orders/return-assessments', '/api/orders/return-assessments/',   self.retassess.pk,   'WAREHOUSE_WORKER'),
            ('orders/return-approvals',   '/api/orders/return-approvals/',     self.retappr.pk,     'MANAGER'),

            ('finance/vouchers',          '/api/finance/vouchers/',            self.voucher.pk,     'ACCOUNTANT'),
            ('finance/payments',          '/api/finance/payments/',            self.payment.pk,     'ACCOUNTANT'),
            ('finance/commissions',       '/api/finance/commissions/',         self.commission.pk,  'ACCOUNTANT'),
            ('finance/balances',          '/api/finance/balances/',            self.balance.pk,     'ACCOUNTANT'),

            ('audit/audit-logs',          '/api/audit/audit-logs/',            self.auditlog.pk,    'MANAGER'),
            ('audit/request-transitions', '/api/audit/request-transitions/',   self.transition.pk,  'MANAGER'),

            ('website/customers',         '/api/website/customers/',           self.profile.pk,     'MANAGER'),
            ('website/catalogs',          '/api/website/catalogs/',            self.catalog.pk,     'MANAGER'),
            ('website/catalog-items',     '/api/website/catalog-items/',       self.catalogitem.pk, 'MANAGER'),
        ]

    def _call(self, method, url):
        return getattr(self.client, method.lower())(url, {}, format='json').status_code

    def test_method_matrix(self):
        rows = []
        for name, list_url, pk, role in self.endpoints:
            self.client.force_authenticate(user=self.users[role])
            detail_url = f'{list_url}{pk}/'
            # Probe inside a savepoint and roll back: a successful DELETE here
            # would otherwise cascade and vanish the fixtures that later
            # endpoints depend on, producing phantom 404s.
            sid = transaction.savepoint()
            try:
                list_codes = {m: self._call(m, list_url) for m in METHODS}
                detail_codes = {m: self._call(m, detail_url) for m in METHODS}
            finally:
                transaction.savepoint_rollback(sid)
            rows.append((name, role, list_codes, detail_codes))

        header = (
            f"\n{'endpoint':<28}{'as role':<19}"
            + ''.join(f'L-{m:<7}' for m in METHODS)
            + ''.join(f'D-{m:<7}' for m in METHODS)
        )
        print(header)
        print('-' * len(header))
        for name, role, lc, dc in rows:
            line = f'{name:<28}{role:<19}'
            line += ''.join(f'{lc[m]:<9}' for m in METHODS)
            line += ''.join(f'{dc[m]:<9}' for m in METHODS)
            print(line)

        print('\nL- = list URL (/thing/)   D- = detail URL (/thing/1/)')
        print('405 = method not routed at that URL shape (by DRF router design)')
        print('403 = routed, role not permitted   400 = routed+permitted, sample payload invalid')

        # Routing invariants. These URL/method pairs are never valid; a 403
        # may legitimately preempt the 405 when the acting role is not
        # permitted the method, since DRF checks permissions before routing.
        for name, role, lc, dc in rows:
            self.assertIn(lc['PUT'], (403, 405), f'{name}: PUT on list URL must not succeed')
            self.assertIn(lc['DELETE'], (403, 405), f'{name}: DELETE on list URL must not succeed')
            self.assertIn(dc['POST'], (403, 405), f'{name}: POST on detail URL must not succeed')

        # Every seeded detail URL must resolve for a role allowed to read it.
        for name, role, lc, dc in rows:
            self.assertNotEqual(
                dc['GET'], 404,
                f'{name}: detail URL 404ed for {role} - seed row missing or queryset over-filtered')
