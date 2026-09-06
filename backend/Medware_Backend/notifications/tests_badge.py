"""The unread badge must count only work that is still waiting.

Reported: the navigation badge read "2" for orders awaiting approval and
stayed at "2" after both were approved. Two separate faults produced it, and
both are pinned here.

The manager's side: a `..._SUBMITTED` notification is a standing request for a
decision, and nothing marked it read when the decision was made.

The salesman's side: the badge counts every unread row, but the Requests page
only ever listed rejections - so an approval counted toward the badge while
appearing on no page that could clear it. A number the user cannot work off is
the same bug wearing different clothes.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from notifications.models import Notification
from orders.models import OrderItem, OrderRequest
from products.models import Product
from users.models import User


class BadgeTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username='bdg_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.other_manager = User.objects.create_user(
            username='bdg_mgr2', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.salesman = User.objects.create_user(
            username='bdg_slm', password='pass', role=User.Role.SALESMAN,
            first_name='Rami', last_name='Haddad', is_verified=True)
        self.customer = Customer.objects.create(
            name='Al Amal Pharmacy', status=Customer.Status.APPROVED)
        self.product = Product.objects.create(name='Gauze', retail_price=Decimal('5.00'))

    def raise_order(self):
        """A salesman's order, created through the API so the notifications
        the manager actually receives are the ones under test."""
        self.client.force_authenticate(self.salesman)
        response = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'notes': '',
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00', 'note': ''}],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def unread_for(self, user, **filters):
        return Notification.objects.filter(
            recipient=user, read_at__isnull=True, **filters).count()

    def badge_count(self, user):
        """Exactly what the navigation bar asks for."""
        self.client.force_authenticate(user)
        response = self.client.get('/api/notifications/', {'unread': 'true'})
        self.assertEqual(response.status_code, 200)
        return len(response.data)


class ManagerBadgeTests(BadgeTestCase):
    def test_approving_an_order_clears_its_review_request(self):
        order_id = self.raise_order()
        self.assertEqual(self.badge_count(self.manager), 1)

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/approve/')

        self.assertEqual(self.badge_count(self.manager), 0)

    def test_rejecting_an_order_clears_its_review_request(self):
        order_id = self.raise_order()

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/reject/',
                         {'notes': 'Prices are wrong'})

        self.assertEqual(self.badge_count(self.manager), 0)

    def test_approving_clears_the_request_for_every_manager(self):
        """The order is no longer waiting on anyone, not just the one who
        ruled on it. Clearing only the actor leaves every other manager
        staring at a decision that has already been made."""
        order_id = self.raise_order()

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/approve/')

        self.assertEqual(self.badge_count(self.other_manager), 0)

    def test_the_exact_reported_case_two_orders_both_approved(self):
        """The badge read 2 and stayed at 2."""
        first, second = self.raise_order(), self.raise_order()
        self.assertEqual(self.badge_count(self.manager), 2)

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{first}/approve/')
        self.client.post(f'/api/orders/order-requests/{second}/approve/')

        self.assertEqual(self.badge_count(self.manager), 0)

    def test_an_undecided_order_still_counts(self):
        first, second = self.raise_order(), self.raise_order()

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{first}/approve/')

        self.assertEqual(self.badge_count(self.manager), 1)
        remaining = Notification.objects.get(
            recipient=self.manager, read_at__isnull=True,
            kind=Notification.Kind.ORDER_SUBMITTED)
        self.assertEqual(remaining.target_id, str(second))

    def test_a_manager_raised_order_leaves_no_request_behind(self):
        """A manager's own order is approved as it is created, so it must not
        add to the badge at all."""
        self.client.force_authenticate(self.manager)
        response = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk, 'notes': '', 'items': [],
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)

        self.assertEqual(self.badge_count(self.manager), 0)


class CustomerRequestBadgeTests(BadgeTestCase):
    def raise_customer(self):
        self.client.force_authenticate(self.salesman)
        response = self.client.post('/api/customers/', {'name': 'New Shop'})
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_approving_a_customer_clears_its_request(self):
        customer_id = self.raise_customer()
        self.assertEqual(self.badge_count(self.manager), 1)

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/customers/{customer_id}/approve/')

        self.assertEqual(self.badge_count(self.manager), 0)

    def test_rejecting_a_customer_clears_its_request(self):
        customer_id = self.raise_customer()

        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/customers/{customer_id}/reject/', {'notes': 'Duplicate'})

        self.assertEqual(self.badge_count(self.manager), 0)


class SalesmanBadgeTests(BadgeTestCase):
    """The badge and the Requests page must agree.

    Anything counted must be listed somewhere the salesman can dismiss it,
    or the number never reaches zero.
    """

    def inbox_items(self, user):
        self.client.force_authenticate(user)
        response = self.client.get('/api/orders/inbox/')
        self.assertEqual(response.status_code, 200)
        return response.data['items']

    def test_an_approval_reaches_the_salesman_inbox(self):
        order_id = self.raise_order()
        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/approve/')

        items = self.inbox_items(self.salesman)

        self.assertEqual([item['kind'] for item in items], ['ORDER_APPROVED'])

    def test_every_counted_notification_is_dismissible(self):
        """The stuck-badge invariant: a row on the badge must carry a
        notification_id, because that is the only thing the page can dismiss."""
        order_id = self.raise_order()
        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/approve/')

        items = self.inbox_items(self.salesman)

        self.assertEqual(len(items), self.badge_count(self.salesman))
        self.assertTrue(all(item['notification_id'] is not None for item in items))

    def test_dismissing_the_approval_clears_the_badge(self):
        order_id = self.raise_order()
        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/approve/')

        item = self.inbox_items(self.salesman)[0]
        self.client.force_authenticate(self.salesman)
        self.client.post(f"/api/notifications/{item['notification_id']}/read/")

        self.assertEqual(self.badge_count(self.salesman), 0)

    def test_a_rejection_still_reaches_the_inbox(self):
        order_id = self.raise_order()
        self.client.force_authenticate(self.manager)
        self.client.post(f'/api/orders/order-requests/{order_id}/reject/', {'notes': 'No'})

        items = self.inbox_items(self.salesman)

        self.assertEqual([item['kind'] for item in items], ['ORDER_REJECTED'])
        self.assertEqual(len(items), self.badge_count(self.salesman))

    def test_a_customer_decision_reaches_the_inbox(self):
        self.client.force_authenticate(self.salesman)
        created = self.client.post('/api/customers/', {'name': 'New Shop'})
        self.client.force_authenticate(self.manager)
        self.client.post(f"/api/customers/{created.data['id']}/approve/")

        items = self.inbox_items(self.salesman)

        self.assertEqual([item['kind'] for item in items], ['CUSTOMER_APPROVED'])
        self.assertEqual(len(items), self.badge_count(self.salesman))

    def test_every_kind_a_salesman_can_receive_is_listed(self):
        """A guard on the fix rather than on one path through it.

        The bug was a kind reaching a salesman that the inbox did not know
        about. Adding a seventh Kind without listing it here brings the stuck
        badge straight back, so the tuples are checked against the enum.
        """
        from orders.views import InboxView

        listed = set(InboxView.ORDER_UPDATE_KINDS) | set(InboxView.CUSTOMER_UPDATE_KINDS)
        addressed_to_salesmen = {
            Notification.Kind.ORDER_APPROVED, Notification.Kind.ORDER_REJECTED,
            Notification.Kind.CUSTOMER_APPROVED, Notification.Kind.CUSTOMER_REJECTED,
        }

        self.assertEqual(listed, addressed_to_salesmen)
