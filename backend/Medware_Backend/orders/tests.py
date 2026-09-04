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


from audit.models import RequestTransition
from notifications.models import Notification
from orders.models import OrderReview


class OrderTransitionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='tr_slm', password='pass', role=User.Role.SALESMAN)
        self.manager = User.objects.create_user(username='tr_mgr', password='pass', role=User.Role.MANAGER)
        self.accountant = User.objects.create_user(username='tr_acc', password='pass', role=User.Role.ACCOUNTANT)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')

    def _order(self, status=OrderRequest.Status.PENDING):
        order = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman, status=status)
        OrderItem.objects.create(order_request=order, product=self.product,
                                 quantity=2, sell_price=Decimal('10.00'))
        return order

    def test_salesman_creates_an_order_with_nested_items(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'notes': 'urgent',
            'items': [
                {'product': self.product.pk, 'quantity': 3, 'sell_price': '10.00', 'note': 'cold chain'},
            ],
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        order = OrderRequest.objects.get(pk=resp.json()['id'])
        self.assertEqual(order.status, OrderRequest.Status.PENDING)
        self.assertEqual(order.salesman, self.salesman)      # server-derived
        self.assertEqual(order.origin, 'SALESMAN')           # server-derived
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().note, 'cold chain')
        self.assertEqual(order.total, Decimal('30.00'))

    def test_creating_an_order_notifies_every_manager(self):
        self.client.force_authenticate(user=self.salesman)

        self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        self.assertTrue(Notification.objects.filter(
            recipient=self.manager, kind=Notification.Kind.ORDER_SUBMITTED).exists())

    def test_manager_created_order_is_born_approved_with_a_review_row(self):
        """Decision (c): every order reaching the accountant has exactly one
        review, even when the manager is its author."""
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        order = OrderRequest.objects.get(pk=resp.json()['id'])
        self.assertEqual(order.status, OrderRequest.Status.APPROVED)
        self.assertEqual(order.origin, 'MANAGER')
        self.assertEqual(order.reviews.count(), 1)
        self.assertEqual(order.reviews.first().manager, self.manager)

    def test_manager_approves_a_pending_order(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(order.status, OrderRequest.Status.APPROVED)
        self.assertEqual(order.reviews.filter(decision='APPROVE').count(), 1)
        self.assertTrue(RequestTransition.objects.filter(
            source_model='OrderRequest', source_id=str(order.pk),
            from_status='PENDING', to_status='APPROVED').exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.salesman, kind=Notification.Kind.ORDER_APPROVED).exists())

    def test_approval_freezes_the_balance_snapshots(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        order.refresh_from_db()
        self.assertEqual(order.previous_balance, Decimal('0.00'))
        self.assertEqual(order.new_balance, Decimal('20.00'))

    def test_salesman_cannot_approve(self):
        """RoleMethodPermission allows SALESMAN to POST on this viewset, so the
        action must check the role itself."""
        order = self._order()
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(order.status, OrderRequest.Status.PENDING)

    def test_accountant_cannot_approve(self):
        order = self._order()
        self.client.force_authenticate(user=self.accountant)

        self.assertEqual(
            self.client.post(f'/api/orders/order-requests/{order.pk}/approve/').status_code, 403)

    def test_approving_an_already_approved_order_is_a_conflict(self):
        order = self._order(status=OrderRequest.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        self.assertEqual(resp.status_code, 409)

    def test_rejecting_without_notes_is_refused(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/reject/',
                                {'notes': '   '}, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(order.status, OrderRequest.Status.PENDING)

    def test_rejecting_with_notes_records_and_notifies_the_reason(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/reject/',
                                {'notes': 'Price above the agreed ceiling'}, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(order.status, OrderRequest.Status.REJECTED)
        review = order.reviews.get(decision='DECLINE')
        self.assertEqual(review.notes, 'Price above the agreed ceiling')
        notification = Notification.objects.get(
            recipient=self.salesman, kind=Notification.Kind.ORDER_REJECTED)
        self.assertIn('Price above the agreed ceiling', notification.message)


class OrderMutationLockTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='lk_slm', password='pass', role=User.Role.SALESMAN)
        self.manager = User.objects.create_user(username='lk_mgr', password='pass', role=User.Role.MANAGER)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')

    def _order(self, status):
        return OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman, status=status)

    def test_manager_can_change_quantities_while_pending(self):
        order = self._order(OrderRequest.Status.PENDING)
        item = OrderItem.objects.create(order_request=order, product=self.product,
                                        quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/orders/order-items/{item.pk}/', {'quantity': 5}, format='json')

        item.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(item.quantity, 5)

    def test_items_cannot_be_added_to_an_approved_order(self):
        """Otherwise a line lands underneath an approval, changing its value."""
        order = self._order(OrderRequest.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/order-items/', {
            'order_request': order.pk, 'product': self.product.pk,
            'quantity': 1, 'sell_price': '10.00',
        }, format='json')

        self.assertEqual(resp.status_code, 409)

    def test_items_cannot_be_edited_on_an_approved_order(self):
        order = self._order(OrderRequest.Status.APPROVED)
        item = OrderItem.objects.create(order_request=order, product=self.product,
                                        quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/orders/order-items/{item.pk}/', {'quantity': 9}, format='json')

        item.refresh_from_db()
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(item.quantity, 2)

    def test_reviews_cannot_be_posted_directly(self):
        """A review posted by hand would walk around the state machine."""
        order = self._order(OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/reviews/', {
            'order': order.pk, 'decision': 'APPROVE', 'notes': '',
        }, format='json')

        order.refresh_from_db()
        # 403, not 405: RoleMethodPermission is default-deny and runs in
        # APIView.dispatch()'s initial() before the handler is selected, so it
        # refuses the write before DRF can report "method not allowed". That
        # default-deny is the guard - the viewset also has no create() method,
        # but we do not rely on that alone.
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(order.status, OrderRequest.Status.PENDING)
