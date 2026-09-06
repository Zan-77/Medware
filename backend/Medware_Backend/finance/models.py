from django.db import models
from django.conf import settings
from django.utils import timezone
from orders.models import OrderRequest


class Voucher(models.Model):
    """A payment received from a customer.

    Raised against the *customer*, not a single order. A shop pays down a
    running balance rather than settling one invoice at a time, so tying a
    voucher to one order made most real payments unrecordable. `order` stays
    for the case where a payment does clear one specific order, and is now
    optional.

    `salesman` is filled from the customer's most recent order rather than
    from the request body - the salesman who raised the order is the one the
    payment belongs to, and letting the accountant type a name would let the
    two disagree.
    """

    number = models.CharField(max_length=50, unique=True)
    # Not auto_now_add: a voucher is often entered days after it was written,
    # and the date on the paper is the one that counts.
    date = models.DateField(default=timezone.localdate)
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.PROTECT, related_name='vouchers')
    order = models.ForeignKey(
        OrderRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vouchers')
    salesman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vouchers')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"Voucher {self.number} ({self.amount})"


class PaymentRecord(models.Model):
    order = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments_recorded')
    date = models.DateTimeField(auto_now_add=True)


class CommissionRecord(models.Model):
    order = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='commissions')
    salesman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='commissions')
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    earned_amount = models.DecimalField(max_digits=12, decimal_places=2)
    adjusted_for_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)


class CustomerBalance(models.Model):
    """Kept for the ledger slice that will maintain it.

    Nothing writes this table today, so it is NOT the source of the balances
    the finance panel shows - those are derived from orders and vouchers in
    `finance.services`. A stored total that nothing maintains reads as zero
    for every customer, which is worse than no number at all.
    """

    customer = models.OneToOneField('customers.Customer', on_delete=models.CASCADE, related_name='balance')
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
