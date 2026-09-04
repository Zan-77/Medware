from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from orders.models import OrderRequest
from users.models import User


class CustomerModelTests(TestCase):
    def test_an_internal_customer_has_no_user_account(self):
        """Outside the website a customer is data, not a login."""
        customer = Customer.objects.create(name='Al Noor Pharmacy', phone='0100000000')

        self.assertIsNone(customer.user)

    def test_a_customer_can_be_linked_to_a_website_account_later(self):
        """The website slice attaches a login to an existing record rather
        than creating a second one."""
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


class CustomerApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='cust_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='cust_slm', password='pass', role=User.Role.SALESMAN)
        self.warehouse = User.objects.create_user(username='cust_wh', password='pass', role=User.Role.WAREHOUSE_WORKER)
        Customer.objects.create(name='Al Noor Pharmacy', phone='0100000000')

    def test_salesman_can_list_customers(self):
        """The order form's customer picker is a salesman-facing screen."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.get('/api/customers/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_manager_can_create_a_customer(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Customer.objects.filter(name='Dar Al Shifa').exists())

    def test_salesman_cannot_create_a_customer(self):
        """Until the e-commerce slice, customer records are entered by staff."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 403)

    def test_warehouse_worker_cannot_read_customers(self):
        self.client.force_authenticate(user=self.warehouse)

        resp = self.client.get('/api/customers/')

        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/customers/').status_code, 401)
