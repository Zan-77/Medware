"""Customer balances, derived from orders and vouchers.

Nothing maintains `CustomerBalance`, so reading it would show every customer
owing zero. These figures are computed per request instead, the same way
`OrderRequest.total` is derived from its lines: a stored total can disagree
with the rows it claims to summarise, and this one already would.

    outstanding = sum(approved order totals) - sum(voucher amounts)
"""

from decimal import Decimal

from django.db.models import DecimalField, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from customers.models import Customer
from orders.models import OrderItem, OrderRequest

from .models import Voucher

# An order lands on the customer's account when a manager approves it.
# PENDING is not owed yet and REJECTED never will be.
BILLABLE_STATUSES = (OrderRequest.Status.APPROVED, OrderRequest.Status.FINALIZED)

MONEY = DecimalField(max_digits=14, decimal_places=2)
ZERO = Value(Decimal('0'), output_field=MONEY)


def _order_total_expression():
    """Sum of quantity x price across the customer's billable order lines."""
    return Subquery(
        OrderItem.objects
        .filter(order_request__customer=OuterRef('pk'),
                order_request__status__in=BILLABLE_STATUSES)
        .values('order_request__customer')
        .annotate(total=Sum(F('quantity') * F('sell_price'), output_field=MONEY))
        .values('total'),
        output_field=MONEY,
    )


def _paid_expression():
    return Subquery(
        Voucher.objects
        .filter(customer=OuterRef('pk'))
        .values('customer')
        .annotate(total=Sum('amount', output_field=MONEY))
        .values('total'),
        output_field=MONEY,
    )


def customer_accounts():
    """Customers annotated with `total_ordered`, `total_paid`, `outstanding`.

    Subqueries rather than joins: joining orders and vouchers in one query
    multiplies the rows against each other, and both sums come out wrong.
    """
    return (
        Customer.objects
        .annotate(
            total_ordered=Coalesce(_order_total_expression(), ZERO, output_field=MONEY),
            total_paid=Coalesce(_paid_expression(), ZERO, output_field=MONEY),
        )
        .annotate(outstanding=F('total_ordered') - F('total_paid'))
    )


def salesman_display(user):
    """Usernames here are generated UUIDs, so show the person's name."""
    if user is None:
        return None
    return user.get_full_name() or user.username


def latest_salesman_names(customer_ids):
    """{customer_id: salesman name} taken from each customer's newest order.

    The salesman on a customer's account is whoever raised their order, so
    there is no salesman until a first order exists. One query, ordered so the
    newest order per customer is the first row seen for that customer.
    """
    names = {}
    orders = (OrderRequest.objects
              .filter(customer_id__in=list(customer_ids), salesman__isnull=False)
              .select_related('salesman')
              .order_by('customer_id', '-created_at'))
    for order in orders:
        names.setdefault(order.customer_id, salesman_display(order.salesman))
    return names


def salesman_for_customer(customer):
    """The user record itself, for stamping onto a new voucher."""
    order = (OrderRequest.objects
             .filter(customer=customer, salesman__isnull=False)
             .select_related('salesman')
             .order_by('-created_at')
             .first())
    return order.salesman if order else None


def billable_orders(customer):
    """The orders that put the customer into debt, oldest first."""
    return (OrderRequest.objects
            .filter(customer=customer, status__in=BILLABLE_STATUSES)
            .select_related('salesman')
            .annotate(line_total=Coalesce(
                Sum(F('items__quantity') * F('items__sell_price'), output_field=MONEY),
                ZERO, output_field=MONEY))
            .order_by('created_at'))
