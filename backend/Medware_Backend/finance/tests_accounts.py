"""Balances are derived, so the arithmetic is the thing worth pinning.

Nothing maintains `CustomerBalance`; these figures come from orders and
vouchers on every request. The risks are the sums going wrong (double
counting when two subqueries become joins), counting orders nobody approved,
and the finance panel opening to roles it does not belong to.
"""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer
from finance.models import Voucher
from orders.models import OrderItem, OrderRequest
from products.models import Product
from users.models import User


def make_user(role, **extra):
    return User.objects.create_user(
        username=f'{role.lower()}-{User.objects.count()}',
        password='pw', role=role, is_verified=True, **extra)


class FinanceAccountTestCase(APITestCase):
    def setUp(self):
        self.accountant = make_user('ACCOUNTANT')
        self.manager = make_user('MANAGER')
        self.salesman = make_user('SALESMAN', first_name='Rami', last_name='Haddad')
        self.customer = Customer.objects.create(
            name='Al Amal Pharmacy', status=Customer.Status.APPROVED)
        self.product = Product.objects.create(name='Gauze', retail_price=Decimal('5.00'))

    def order(self, status_value=OrderRequest.Status.APPROVED, quantity=2,
              price='10.00', salesman=False):
        # `salesman=False` means "use the default"; None is a real value here,
        # standing for an order a manager raised.
        order = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, status=status_value,
            salesman=self.salesman if salesman is False else salesman)
        OrderItem.objects.create(order_request=order, product=self.product,
                                 quantity=quantity, sell_price=Decimal(price))
        return order

    def voucher(self, number, amount, **extra):
        return Voucher.objects.create(
            number=number, customer=self.customer, amount=Decimal(amount),
            date=date(2026, 1, 1), **extra)


class BalanceArithmeticTests(FinanceAccountTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.accountant)
        self.url = reverse('customer-account-list')

    def row(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return next(r for r in response.data if r['customer'] == self.customer.pk)

    def test_a_customer_with_no_activity_owes_nothing(self):
        row = self.row()
        self.assertEqual(row['total_ordered'], 0)
        self.assertEqual(row['total_paid'], 0)
        self.assertEqual(row['outstanding'], 0)

    def test_an_approved_order_raises_the_balance(self):
        self.order(quantity=2, price='10.00')

        self.assertEqual(self.row()['outstanding'], 20)

    def test_a_voucher_lowers_the_balance(self):
        self.order(quantity=2, price='10.00')
        self.voucher('V-1', '7.50')

        row = self.row()
        self.assertEqual(row['total_ordered'], 20)
        self.assertEqual(row['total_paid'], Decimal('7.50'))
        self.assertEqual(row['outstanding'], Decimal('12.50'))

    def test_several_orders_and_vouchers_are_not_multiplied_together(self):
        """The join trap: two orders and two vouchers gathered in one query
        would count each order twice and each voucher twice."""
        self.order(quantity=1, price='10.00')
        self.order(quantity=1, price='20.00')
        self.voucher('V-1', '5.00')
        self.voucher('V-2', '3.00')

        row = self.row()
        self.assertEqual(row['total_ordered'], 30)
        self.assertEqual(row['total_paid'], 8)
        self.assertEqual(row['outstanding'], 22)

    def test_a_pending_order_is_not_owed_yet(self):
        self.order(status_value=OrderRequest.Status.PENDING)

        self.assertEqual(self.row()['total_ordered'], 0)

    def test_a_rejected_order_never_counts(self):
        self.order(status_value=OrderRequest.Status.REJECTED)

        self.assertEqual(self.row()['total_ordered'], 0)

    def test_a_finalized_order_still_counts(self):
        self.order(status_value=OrderRequest.Status.FINALIZED, quantity=3, price='10.00')

        self.assertEqual(self.row()['total_ordered'], 30)

    def test_overpayment_shows_as_a_negative_balance(self):
        """Better a visible credit than a floor at zero hiding the mistake."""
        self.order(quantity=1, price='10.00')
        self.voucher('V-1', '15.00')

        self.assertEqual(self.row()['outstanding'], -5)

    def test_one_customer_balance_does_not_leak_into_another(self):
        other = Customer.objects.create(name='Nour', status=Customer.Status.APPROVED)
        self.order(quantity=1, price='10.00')

        response = self.client.get(self.url)
        row = next(r for r in response.data if r['customer'] == other.pk)
        self.assertEqual(row['outstanding'], 0)

    def test_a_customer_awaiting_approval_is_not_listed(self):
        pending = Customer.objects.create(name='Waiting', status=Customer.Status.PENDING)

        response = self.client.get(self.url)
        self.assertNotIn(pending.pk, [r['customer'] for r in response.data])


class SalesmanNameTests(FinanceAccountTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.accountant)
        self.url = reverse('customer-account-list')

    def row(self):
        return next(r for r in self.client.get(self.url).data
                    if r['customer'] == self.customer.pk)

    def test_the_salesman_is_the_one_who_raised_the_order(self):
        self.order()

        self.assertEqual(self.row()['salesman_name'], 'Rami Haddad')

    def test_a_customer_with_no_orders_has_no_salesman_yet(self):
        self.assertIsNone(self.row()['salesman_name'])

    def test_the_most_recent_order_wins(self):
        self.order()
        later = make_user('SALESMAN', first_name='Sara', last_name='Nassar')
        self.order(salesman=later)

        self.assertEqual(self.row()['salesman_name'], 'Sara Nassar')

    def test_a_manager_raised_order_leaves_the_salesman_unset(self):
        """A manager's order genuinely has no salesman. Reaching past it to an
        older order would name someone the newest order had nothing to do
        with."""
        self.order()
        self.order(salesman=None)

        self.assertIsNone(self.row()['salesman_name'])

    def test_a_pending_order_does_not_supply_the_salesman(self):
        """The bug this closes: a customer whose balance came from a manager's
        order showed the salesman of a *pending* order instead. Nothing in the
        balance belonged to that salesman."""
        self.order(salesman=None)
        self.order(status_value=OrderRequest.Status.PENDING)

        self.assertIsNone(self.row()['salesman_name'])

    def test_a_rejected_order_does_not_supply_the_salesman(self):
        self.order(status_value=OrderRequest.Status.REJECTED)

        self.assertIsNone(self.row()['salesman_name'])

    def test_a_customer_with_only_a_pending_order_has_no_salesman(self):
        self.order(status_value=OrderRequest.Status.PENDING)

        self.assertIsNone(self.row()['salesman_name'])


class StatementTests(FinanceAccountTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.accountant)
        self.url = reverse('customer-account-statement', args=[self.customer.pk])

    def test_it_lists_the_orders_that_raised_the_balance(self):
        order = self.order(quantity=2, price='10.00')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([o['id'] for o in response.data['orders']], [order.pk])
        self.assertEqual(response.data['orders'][0]['total'], 20)
        self.assertIsNotNone(response.data['orders'][0]['date'])

    def test_it_lists_the_vouchers_that_lowered_it(self):
        voucher = self.voucher('V-9', '4.00')

        response = self.client.get(self.url)
        self.assertEqual(response.data['vouchers'][0]['id'], voucher.pk)
        self.assertEqual(response.data['vouchers'][0]['number'], 'V-9')
        self.assertEqual(response.data['vouchers'][0]['date'], '2026-01-01')

    def test_it_omits_orders_that_were_never_approved(self):
        self.order(status_value=OrderRequest.Status.PENDING)

        self.assertEqual(self.client.get(self.url).data['orders'], [])

    def test_it_carries_the_same_totals_as_the_list_row(self):
        self.order(quantity=2, price='10.00')
        self.voucher('V-1', '5.00')

        response = self.client.get(self.url)
        self.assertEqual(response.data['outstanding'], 15)
        self.assertEqual(response.data['customer_name'], 'Al Amal Pharmacy')

    def test_another_customers_rows_stay_out_of_the_statement(self):
        other = Customer.objects.create(name='Nour', status=Customer.Status.APPROVED)
        Voucher.objects.create(number='V-OTHER', customer=other,
                               amount=Decimal('50.00'), date=date(2026, 1, 1))

        response = self.client.get(self.url)
        self.assertEqual(response.data['vouchers'], [])


class VoucherCreateTests(FinanceAccountTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.accountant)
        self.url = reverse('voucher-list')

    def payload(self, **overrides):
        return {'number': 'V-100', 'date': '2026-03-01',
                'customer': self.customer.pk, 'amount': '25.00', **overrides}

    def test_an_accountant_can_raise_a_voucher(self):
        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['date'], '2026-03-01')

    def test_the_date_is_the_one_supplied_not_today(self):
        """It was auto_now_add before, so a voucher written last week could
        only ever be recorded as written today."""
        self.client.post(self.url, self.payload())

        self.assertEqual(Voucher.objects.get().date, date(2026, 3, 1))

    def test_the_salesman_is_taken_from_the_customers_order(self):
        self.order()

        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.data['salesman'], self.salesman.pk)
        self.assertEqual(response.data['salesman_name'], 'Rami Haddad')

    def test_a_pending_order_does_not_put_a_salesman_on_the_voucher(self):
        """The reported bug, at the point it actually mattered: the voucher
        was stamped with the salesman of an order that was not being paid."""
        self.order(salesman=None)
        self.order(status_value=OrderRequest.Status.PENDING)

        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIsNone(response.data['salesman'])
        self.assertIsNone(response.data['salesman_name'])

    def test_a_customer_with_no_billable_orders_gets_no_salesman(self):
        response = self.client.post(self.url, self.payload())

        self.assertIsNone(response.data['salesman'])

    def test_a_salesman_named_in_the_request_body_is_ignored(self):
        self.order()
        impostor = make_user('SALESMAN', first_name='Wrong', last_name='Person')

        response = self.client.post(self.url, self.payload(salesman=impostor.pk))

        self.assertEqual(response.data['salesman'], self.salesman.pk)

    def test_a_voucher_number_cannot_repeat(self):
        self.client.post(self.url, self.payload())

        response = self.client.post(self.url, self.payload(amount='5.00'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_voucher_needs_no_order(self):
        """A payment settles a running balance, not one invoice."""
        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['order'])

    def test_a_voucher_cannot_name_another_customers_order(self):
        other = Customer.objects.create(name='Nour', status=Customer.Status.APPROVED)
        foreign = OrderRequest.objects.create(
            origin='SALESMAN', customer=other, status=OrderRequest.Status.APPROVED)

        response = self.client.post(self.url, self.payload(order=foreign.pk))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_negative_amount_is_refused(self):
        response = self.client.post(self.url, self.payload(amount='-5.00'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_customer_awaiting_approval_cannot_be_paid_against(self):
        pending = Customer.objects.create(name='Waiting', status=Customer.Status.PENDING)

        response = self.client.post(self.url, self.payload(customer=pending.pk))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_a_manager_can_raise_a_voucher(self):
        self.client.force_authenticate(self.manager)

        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)


class FinanceAccessTests(FinanceAccountTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('customer-account-list')

    def test_an_accountant_may_read_the_accounts(self):
        self.client.force_authenticate(self.accountant)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_a_manager_may_read_the_accounts(self):
        self.client.force_authenticate(self.manager)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_a_salesman_may_not(self):
        self.client.force_authenticate(self.salesman)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_a_warehouse_worker_may_not(self):
        self.client.force_authenticate(make_user('WAREHOUSE_WORKER'))

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_an_unverified_accountant_may_not(self):
        unverified = User.objects.create_user(
            username='new-accountant', password='pw', role='ACCOUNTANT', is_verified=False)
        self.client.force_authenticate(unverified)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_a_signed_out_visitor_may_not(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_the_accounts_are_read_only(self):
        self.client.force_authenticate(self.accountant)

        response = self.client.post(self.url, {'customer_name': 'Invented'})

        self.assertIn(response.status_code,
                      (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED))
