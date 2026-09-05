from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import RequestTransition
from customers.models import Customer
from notifications.models import Notification
from orders.models import OrderRequest
from users.models import User


class CustomerModelTests(TestCase):
    def test_an_internal_customer_has_no_user_account(self):
        """Outside the website a customer is data, not a login."""
        customer = Customer.objects.create(name='Al Noor Pharmacy', phone='0100000000')

        self.assertIsNone(customer.user)

    def test_a_customer_can_be_linked_to_a_website_account_later(self):
        customer = Customer.objects.create(name='Al Noor Pharmacy')
        account = User.objects.create_user(username='alnoor', password='pass', role=User.Role.CUSTOMER)

        customer.user = account
        customer.save()

        self.assertEqual(account.customer, customer)

    def test_deleting_a_customer_with_orders_is_refused(self):
        """PROTECT: order history must never cascade away with the customer."""
        customer = Customer.objects.create(name='Al Noor Pharmacy')
        OrderRequest.objects.create(origin='SALESMAN', customer=customer)

        with self.assertRaises(ProtectedError):
            customer.delete()

    def test_a_new_customer_starts_pending(self):
        self.assertEqual(Customer.objects.create(name='Dar Al Shifa').status,
                         Customer.Status.PENDING)


class CustomerCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='cc_mgr', password='pass', role=User.Role.MANAGER)
        self.other_manager = User.objects.create_user(username='cc_mgr2', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='cc_slm', password='pass', role=User.Role.SALESMAN)
        self.warehouse = User.objects.create_user(username='cc_wh', password='pass', role=User.Role.WAREHOUSE_WORKER)

    def test_a_salesman_creates_a_customer_as_a_pending_request(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 201)
        customer = Customer.objects.get(pk=resp.json()['id'])
        self.assertEqual(customer.status, Customer.Status.PENDING)
        self.assertEqual(customer.created_by, self.salesman)

    def test_a_salesman_creating_a_customer_notifies_every_manager(self):
        self.client.force_authenticate(user=self.salesman)

        self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        for manager in (self.manager, self.other_manager):
            self.assertTrue(Notification.objects.filter(
                recipient=manager, kind=Notification.Kind.CUSTOMER_SUBMITTED).exists())

    def test_a_manager_creates_a_customer_already_approved(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        customer = Customer.objects.get(pk=resp.json()['id'])
        self.assertEqual(customer.status, Customer.Status.APPROVED)
        self.assertEqual(customer.created_by, self.manager)

    def test_a_manager_created_customer_does_not_notify_anyone(self):
        """Nothing is waiting on it, so nobody needs telling."""
        self.client.force_authenticate(user=self.manager)

        self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(Notification.objects.count(), 0)

    def test_creation_writes_an_audit_row(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertTrue(RequestTransition.objects.filter(
            source_model='Customer', source_id=str(resp.json()['id']),
            to_status='PENDING').exists())

    def test_a_warehouse_worker_cannot_create_a_customer(self):
        self.client.force_authenticate(user=self.warehouse)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 403)

    def test_a_warehouse_worker_cannot_read_customers(self):
        self.client.force_authenticate(user=self.warehouse)

        self.assertEqual(self.client.get('/api/customers/').status_code, 403)

    def test_status_cannot_be_set_from_the_request_body(self):
        """The regression guard: status moves only through the actions."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/',
                                {'name': 'Dar Al Shifa', 'status': 'APPROVED'}, format='json')

        self.assertEqual(Customer.objects.get(pk=resp.json()['id']).status,
                         Customer.Status.PENDING)

    def test_status_cannot_be_changed_by_patching(self):
        """The real read_only_fields guard. Unlike the create path - where
        perform_create passes status= explicitly and would mask a writable
        field - nothing here overrides the serializer, so this fails if
        `status` ever leaves read_only_fields."""
        self.client.force_authenticate(user=self.salesman)
        created = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')
        customer_id = created.json()['id']

        self.client.patch(f'/api/customers/{customer_id}/',
                          {'status': 'APPROVED'}, format='json')

        self.assertEqual(Customer.objects.get(pk=customer_id).status,
                         Customer.Status.PENDING)


class CustomerScopingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='cs_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='cs_slm', password='pass', role=User.Role.SALESMAN)
        self.other_salesman = User.objects.create_user(username='cs_slm2', password='pass', role=User.Role.SALESMAN)

        self.approved = Customer.objects.create(name='Approved Co', status=Customer.Status.APPROVED)
        self.mine = Customer.objects.create(name='My Pending', status=Customer.Status.PENDING,
                                            created_by=self.salesman)
        self.theirs = Customer.objects.create(name='Their Pending', status=Customer.Status.PENDING,
                                              created_by=self.other_salesman)

    def test_a_manager_sees_every_customer(self):
        self.client.force_authenticate(user=self.manager)

        names = {row['name'] for row in self.client.get('/api/customers/').json()}

        self.assertEqual(names, {'Approved Co', 'My Pending', 'Their Pending'})

    def test_a_salesman_sees_approved_customers_and_only_their_own_pending(self):
        self.client.force_authenticate(user=self.salesman)

        names = {row['name'] for row in self.client.get('/api/customers/').json()}

        self.assertEqual(names, {'Approved Co', 'My Pending'})

    def test_the_status_filter_narrows_the_list(self):
        self.client.force_authenticate(user=self.manager)

        rows = self.client.get('/api/customers/?status=PENDING').json()

        self.assertEqual({row['name'] for row in rows}, {'My Pending', 'Their Pending'})

    def test_an_unknown_status_is_rejected(self):
        self.client.force_authenticate(user=self.manager)

        self.assertEqual(self.client.get('/api/customers/?status=NOPE').status_code, 400)

    def test_the_list_carries_the_creator_name(self):
        self.client.force_authenticate(user=self.manager)

        rows = self.client.get('/api/customers/?status=PENDING').json()

        self.assertEqual({row['created_by_name'] for row in rows}, {'cs_slm', 'cs_slm2'})

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/customers/').status_code, 401)

    def test_a_salesman_cannot_edit_another_salesmans_customer(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/customers/{self.theirs.pk}/',
                                 {'name': 'Hijacked'}, format='json')

        self.theirs.refresh_from_db()
        self.assertIn(resp.status_code, (403, 404))
        self.assertEqual(self.theirs.name, 'Their Pending')

    def test_a_salesman_cannot_edit_an_approved_customer(self):
        """Editing after a manager approved it changes what was approved."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/customers/{self.approved.pk}/',
                                 {'name': 'Renamed'}, format='json')

        self.approved.refresh_from_db()
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(self.approved.name, 'Approved Co')

    def test_a_salesman_can_edit_their_own_pending_customer(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/customers/{self.mine.pk}/',
                                 {'name': 'Corrected Name'}, format='json')

        self.mine.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.mine.name, 'Corrected Name')

    def test_a_manager_can_edit_any_customer(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/customers/{self.theirs.pk}/',
                                 {'name': 'Manager Edit'}, format='json')

        self.theirs.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.theirs.name, 'Manager Edit')


class CustomerTransitionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='ct_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='ct_slm', password='pass', role=User.Role.SALESMAN)
        self.accountant = User.objects.create_user(username='ct_acc', password='pass', role=User.Role.ACCOUNTANT)

    def _pending(self):
        return Customer.objects.create(name='Dar Al Shifa', status=Customer.Status.PENDING,
                                       created_by=self.salesman)

    def test_a_manager_approves_a_pending_customer(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/approve/')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(customer.status, Customer.Status.APPROVED)
        self.assertTrue(RequestTransition.objects.filter(
            source_model='Customer', source_id=str(customer.pk),
            from_status='PENDING', to_status='APPROVED').exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.salesman, kind=Notification.Kind.CUSTOMER_APPROVED).exists())

    def test_a_salesman_cannot_approve(self):
        """RoleMethodPermission allows SALESMAN to POST here, so the action
        must check the role itself."""
        customer = self._pending()
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/customers/{customer.pk}/approve/')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(customer.status, Customer.Status.PENDING)

    def test_an_accountant_cannot_approve(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.accountant)

        self.assertEqual(
            self.client.post(f'/api/customers/{customer.pk}/approve/').status_code, 403)

    def test_approving_an_already_approved_customer_is_a_conflict(self):
        customer = Customer.objects.create(name='Done', status=Customer.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        self.assertEqual(
            self.client.post(f'/api/customers/{customer.pk}/approve/').status_code, 409)

    def test_rejecting_without_notes_is_refused(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/reject/',
                                {'notes': '   '}, format='json')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(customer.status, Customer.Status.PENDING)

    def test_rejecting_records_and_notifies_the_reason(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/reject/',
                                {'notes': 'Duplicate of an existing account'}, format='json')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(customer.status, Customer.Status.REJECTED)
        self.assertEqual(customer.rejection_notes, 'Duplicate of an existing account')
        notification = Notification.objects.get(
            recipient=self.salesman, kind=Notification.Kind.CUSTOMER_REJECTED)
        self.assertIn('Duplicate of an existing account', notification.message)

    def test_a_customer_created_without_a_creator_still_rejects_cleanly(self):
        """`created_by` is SET_NULL, so the notify list can be empty."""
        customer = Customer.objects.create(name='Orphan', status=Customer.Status.PENDING)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/reject/',
                                {'notes': 'No owner'}, format='json')

        self.assertEqual(resp.status_code, 200)
