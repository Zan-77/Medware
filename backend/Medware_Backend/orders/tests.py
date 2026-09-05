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
        self.salesman = User.objects.create_user(username='st_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
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
        self.salesman = User.objects.create_user(username='tr_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.manager = User.objects.create_user(username='tr_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.accountant = User.objects.create_user(username='tr_acc', password='pass', role=User.Role.ACCOUNTANT, is_verified=True)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy', status=Customer.Status.APPROVED)
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
        self.salesman = User.objects.create_user(username='lk_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.manager = User.objects.create_user(username='lk_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
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

    def test_posting_an_item_without_an_order_is_a_validation_error(self):
        """`order_request` is optional on the serializer for nested creation,
        so a direct POST that omits it must 400 rather than raise KeyError."""
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/order-items/', {
            'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00',
        }, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('order_request', resp.json())

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


from notifications.services import notify


class InboxTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='ib_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.other_salesman = User.objects.create_user(username='ib_slm2', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.manager = User.objects.create_user(username='ib_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.accountant = User.objects.create_user(username='ib_acc', password='pass', role=User.Role.ACCOUNTANT, is_verified=True)
        self.warehouse = User.objects.create_user(username='ib_wh', password='pass', role=User.Role.WAREHOUSE_WORKER, is_verified=True)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy', status=Customer.Status.APPROVED)

        self.pending = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.PENDING)
        self.approved = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.APPROVED)

    def test_manager_inbox_holds_the_pending_orders(self):
        self.client.force_authenticate(user=self.manager)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['role'], 'MANAGER')
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['order']['id'], self.pending.pk)
        self.assertEqual(body['items'][0]['kind'], 'ORDER_PENDING')

    def test_accountant_inbox_holds_the_approved_orders(self):
        self.client.force_authenticate(user=self.accountant)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual([i['order']['id'] for i in body['items']], [self.approved.pk])

    def test_warehouse_inbox_is_empty_until_finance_lands(self):
        self.client.force_authenticate(user=self.warehouse)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['count'], 0)

    def test_salesman_inbox_holds_their_unread_rejections_only(self):
        rejected = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.REJECTED)
        mine = notify([self.salesman], Notification.Kind.ORDER_REJECTED, rejected,
                      message='Order rejected: too expensive')[0]
        notify([self.other_salesman], Notification.Kind.ORDER_REJECTED, rejected,
               message='Not yours')

        self.client.force_authenticate(user=self.salesman)
        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['notification_id'], mine.pk)
        self.assertEqual(body['items'][0]['order']['id'], rejected.pk)

    def test_a_read_rejection_leaves_the_salesman_inbox(self):
        rejected = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.REJECTED)
        row = notify([self.salesman], Notification.Kind.ORDER_REJECTED, rejected, message='x')[0]
        self.client.force_authenticate(user=self.salesman)

        self.client.post(f'/api/notifications/{row.pk}/read/')

        self.assertEqual(self.client.get('/api/orders/inbox/').json()['count'], 0)

    def test_customer_cannot_read_the_inbox(self):
        account = User.objects.create_user(username='ib_cust', password='pass', role=User.Role.CUSTOMER)
        self.client.force_authenticate(user=account)

        self.assertEqual(self.client.get('/api/orders/inbox/').status_code, 403)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/orders/inbox/').status_code, 401)

    def test_a_notification_with_a_non_order_target_is_skipped(self):
        """`target_id` is generic and will carry non-order targets; one bad
        row must not 500 the whole inbox."""
        Notification.objects.create(
            recipient=self.salesman,
            kind=Notification.Kind.ORDER_REJECTED,
            target_type='SupplierBill',
            target_id='not-an-order',
            message='unrelated',
        )
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.get('/api/orders/inbox/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 0)


class OrderListFilterTests(TestCase):
    """The spec requires ?status= and ?customer= to filter the order list.

    Before this, neither was implemented and both were silently discarded -
    `getOrders('PENDING')` returned every order in the system.
    """

    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='fl_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.client.force_authenticate(user=self.manager)

        self.customer_a = Customer.objects.create(name='Al Noor Pharmacy')
        self.customer_b = Customer.objects.create(name='Dar Al Shifa')

        self.pending = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer_a, status=OrderRequest.Status.PENDING)
        self.approved = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer_b, status=OrderRequest.Status.APPROVED)

    def test_status_narrows_the_list(self):
        resp = self.client.get('/api/orders/order-requests/?status=PENDING')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.pending.pk])

    def test_customer_narrows_the_list(self):
        resp = self.client.get(f'/api/orders/order-requests/?customer={self.customer_b.pk}')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([row['id'] for row in resp.json()], [self.approved.pk])

    def test_no_filter_returns_everything(self):
        resp = self.client.get('/api/orders/order-requests/')

        self.assertEqual(len(resp.json()), 2)

    def test_an_unknown_status_is_rejected(self):
        """A typo must fail loudly rather than silently returning every row."""
        resp = self.client.get('/api/orders/order-requests/?status=NOT_A_STATUS')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('status', resp.json())

    def test_a_non_numeric_customer_is_rejected(self):
        resp = self.client.get('/api/orders/order-requests/?customer=abc')

        self.assertEqual(resp.status_code, 400)


class OrderMutationGuardTests(TestCase):
    """Guards found by the final whole-branch review."""

    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='mg_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.other_salesman = User.objects.create_user(username='mg_slm2', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.manager = User.objects.create_user(username='mg_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.accountant = User.objects.create_user(username='mg_acc', password='pass', role=User.Role.ACCOUNTANT, is_verified=True)
        self.customer_a = Customer.objects.create(name='Al Noor Pharmacy', status=Customer.Status.APPROVED)
        self.customer_b = Customer.objects.create(name='Dar Al Shifa', status=Customer.Status.APPROVED)
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')

    def _order(self, status, salesman=None):
        return OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer_a,
            salesman=salesman or self.salesman, status=status)

    def test_an_approved_order_cannot_be_repointed_at_another_customer(self):
        order = self._order(OrderRequest.Status.APPROVED)
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/orders/order-requests/{order.pk}/',
                                 {'customer': self.customer_b.pk}, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(order.customer_id, self.customer_a.pk)

    def test_a_pending_order_can_still_be_edited(self):
        order = self._order(OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/orders/order-requests/{order.pk}/',
                                 {'notes': 'updated'}, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(order.notes, 'updated')

    def test_a_nested_item_carrying_order_request_does_not_500(self):
        # The nested `order_request` must name a real row - a nonexistent pk
        # (e.g. 999) is rejected by the field's own PrimaryKeyRelatedField
        # validation with 400 before create() ever runs, which would test FK
        # validation rather than the TypeError this guards against. A decoy
        # order that actually exists proves the parent order wins instead of
        # the nested value leaking through.
        decoy = self._order(OrderRequest.Status.PENDING, salesman=self.other_salesman)
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer_a.pk,
            'items': [{'order_request': decoy.pk, 'product': self.product.pk,
                       'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        order = OrderRequest.objects.get(pk=resp.json()['id'])
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().order_request_id, order.pk)
        self.assertEqual(decoy.items.count(), 0)

    def test_patching_items_is_a_validation_error_not_a_500(self):
        order = self._order(OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/orders/order-requests/{order.pk}/', {
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('items', resp.json())

    def test_a_customer_cannot_create_an_order(self):
        account = User.objects.create_user(username='mg_cust', password='pass', role=User.Role.CUSTOMER)
        self.client.force_authenticate(user=account)

        resp = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer_b.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        self.assertEqual(resp.status_code, 403)

    def test_a_salesman_can_add_an_item_to_their_own_pending_order(self):
        order = self._order(OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/orders/order-items/', {
            'order_request': order.pk, 'product': self.product.pk,
            'quantity': 2, 'sell_price': '10.00',
        }, format='json')

        self.assertEqual(resp.status_code, 201)

    def test_a_salesman_cannot_add_an_item_to_someone_elses_order(self):
        order = self._order(OrderRequest.Status.PENDING, salesman=self.other_salesman)
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/orders/order-items/', {
            'order_request': order.pk, 'product': self.product.pk,
            'quantity': 2, 'sell_price': '10.00',
        }, format='json')

        self.assertEqual(resp.status_code, 403)

    def test_an_accountant_cannot_edit_order_items(self):
        order = self._order(OrderRequest.Status.PENDING)
        item = OrderItem.objects.create(order_request=order, product=self.product,
                                        quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.accountant)

        resp = self.client.patch(f'/api/orders/order-items/{item.pk}/',
                                 {'quantity': 9}, format='json')

        item.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(item.quantity, 2)

    def test_order_items_carry_the_product_name(self):
        order = self._order(OrderRequest.Status.PENDING)
        OrderItem.objects.create(order_request=order, product=self.product,
                                 quantity=1, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.manager)

        row = self.client.get(f'/api/orders/order-requests/{order.pk}/').json()

        self.assertEqual(row['items'][0]['product_name'], 'Paracetamol')


from customers.models import Customer as CustomerModel


class OrderRequiresApprovedCustomerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='ac_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')
        self.client.force_authenticate(user=self.salesman)

    def _post(self, customer):
        return self.client.post('/api/orders/order-requests/', {
            'customer': customer.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

    def test_an_order_for_an_approved_customer_is_accepted(self):
        customer = CustomerModel.objects.create(name='Approved Co',
                                                status=CustomerModel.Status.APPROVED)

        self.assertEqual(self._post(customer).status_code, 201)

    def test_an_order_for_a_pending_customer_is_refused(self):
        """An order approved against a customer the company has not accepted
        is a record nobody can act on."""
        customer = CustomerModel.objects.create(name='Pending Co',
                                                status=CustomerModel.Status.PENDING,
                                                created_by=self.salesman)

        resp = self._post(customer)

        self.assertEqual(resp.status_code, 400)
        self.assertIn('customer', resp.json())

    def test_an_order_for_a_rejected_customer_is_refused(self):
        customer = CustomerModel.objects.create(name='Rejected Co',
                                                status=CustomerModel.Status.REJECTED,
                                                created_by=self.salesman)

        self.assertEqual(self._post(customer).status_code, 400)


class InboxCustomerRowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='ic_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.salesman = User.objects.create_user(username='ic_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)

    def test_the_manager_inbox_carries_pending_customers(self):
        pending = CustomerModel.objects.create(name='Pending Co',
                                               status=CustomerModel.Status.PENDING,
                                               created_by=self.salesman)
        CustomerModel.objects.create(name='Approved Co', status=CustomerModel.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        body = self.client.get('/api/orders/inbox/').json()

        customer_rows = [i for i in body['items'] if i['kind'] == 'CUSTOMER_PENDING']
        self.assertEqual(len(customer_rows), 1)
        self.assertEqual(customer_rows[0]['customer']['id'], pending.pk)
        self.assertIsNone(customer_rows[0]['order'])

    def test_the_salesman_inbox_carries_their_unread_customer_rejections(self):
        rejected = CustomerModel.objects.create(name='Rejected Co',
                                                status=CustomerModel.Status.REJECTED,
                                                created_by=self.salesman)
        row = notify([self.salesman], Notification.Kind.CUSTOMER_REJECTED, rejected,
                     message='Customer Rejected Co was rejected: duplicate')[0]
        self.client.force_authenticate(user=self.salesman)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['kind'], 'CUSTOMER_REJECTED')
        self.assertEqual(body['items'][0]['notification_id'], row.pk)
        self.assertEqual(body['items'][0]['customer']['id'], rejected.pk)

    def test_order_rows_still_carry_a_null_customer_key(self):
        customer = CustomerModel.objects.create(name='Approved Co',
                                                status=CustomerModel.Status.APPROVED)
        OrderRequest.objects.create(origin='SALESMAN', customer=customer,
                                    salesman=self.salesman,
                                    status=OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.manager)

        body = self.client.get('/api/orders/inbox/').json()

        order_rows = [i for i in body['items'] if i['kind'] == 'ORDER_PENDING']
        self.assertEqual(len(order_rows), 1)
        self.assertIsNone(order_rows[0]['customer'])
