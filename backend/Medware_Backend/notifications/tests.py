from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from notifications.models import Notification
from notifications.services import managers, notify
from orders.models import OrderRequest
from users.models import User


class NotifyServiceTests(TestCase):
    def setUp(self):
        self.manager_a = User.objects.create_user(username='nt_mgr_a', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.manager_b = User.objects.create_user(username='nt_mgr_b', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.salesman = User.objects.create_user(username='nt_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.order = OrderRequest.objects.create(origin='SALESMAN', customer=self.customer, salesman=self.salesman)

    def test_managers_returns_every_manager_and_nobody_else(self):
        found = set(managers().values_list('username', flat=True))

        self.assertEqual(found, {'nt_mgr_a', 'nt_mgr_b'})

    def test_notify_creates_one_row_per_recipient_pointing_at_the_target(self):
        created = notify(managers(), Notification.Kind.ORDER_SUBMITTED, self.order, message='New order')

        self.assertEqual(len(created), 2)
        row = Notification.objects.get(recipient=self.manager_a)
        self.assertEqual(row.kind, Notification.Kind.ORDER_SUBMITTED)
        self.assertEqual(row.target_type, 'OrderRequest')
        self.assertEqual(row.target_id, str(self.order.pk))
        self.assertIsNone(row.read_at)

    def test_notify_tolerates_an_empty_recipient_list(self):
        """A manager-created order may have no salesman to notify."""
        created = notify([], Notification.Kind.ORDER_APPROVED, self.order)

        self.assertEqual(created, [])
        self.assertEqual(Notification.objects.count(), 0)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='na_slm', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.other = User.objects.create_user(username='na_other', password='pass', role=User.Role.SALESMAN, is_verified=True)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.order = OrderRequest.objects.create(origin='SALESMAN', customer=self.customer, salesman=self.salesman)
        self.mine = notify([self.salesman], Notification.Kind.ORDER_REJECTED, self.order, message='Too expensive')[0]
        notify([self.other], Notification.Kind.ORDER_REJECTED, self.order, message='Not yours')

    def test_listing_returns_only_my_notifications(self):
        self.client.force_authenticate(user=self.salesman)

        rows = self.client.get('/api/notifications/').json()

        self.assertEqual([r['id'] for r in rows], [self.mine.pk])
        self.assertEqual(rows[0]['message'], 'Too expensive')

    def test_unread_filter_hides_read_rows(self):
        self.client.force_authenticate(user=self.salesman)
        self.client.post(f'/api/notifications/{self.mine.pk}/read/')

        self.assertEqual(self.client.get('/api/notifications/?unread=true').json(), [])
        self.assertEqual(len(self.client.get('/api/notifications/').json()), 1)

    def test_marking_read_sets_the_timestamp(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/notifications/{self.mine.pk}/read/')

        self.mine.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(self.mine.read_at)

    def test_cannot_mark_someone_elses_notification_read(self):
        theirs = Notification.objects.exclude(pk=self.mine.pk).first()
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/notifications/{theirs.pk}/read/')

        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/notifications/').status_code, 401)
