from decimal import Decimal

from django.db import models
from products.models import Product
from users.models import User


class OrderRequest(models.Model):
    ORIGIN_CHOICES = [
        ('SALESMAN', 'Salesman'),
        ('MANAGER', 'Manager'),
        ('CUSTOMER', 'Customer'),
    ]

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending manager review'
        APPROVED = 'APPROVED', 'Approved - awaiting accountant'
        REJECTED = 'REJECTED', 'Rejected by manager'
        FINALIZED = 'FINALIZED', 'Finalized by accountant'

    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='order_requests')
    salesman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='salesman_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    # Frozen when the manager approves. Computed live, reopening an old order
    # would show today's balance rather than the one the customer agreed to.
    previous_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    new_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    @property
    def total(self):
        """Derived, never stored - a stored total can disagree with its lines."""
        return sum((item.line_total for item in self.items.all()), Decimal('0'))

    def __str__(self):
        return f"OrderRequest {self.id} ({self.status})"


class OrderItem(models.Model):
    order_request = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    # Copied from the product when the line is added, then editable. A later
    # change to Product.retail_price must not restate a historical order.
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)
    return_quantity = models.IntegerField(default=0)

    @property
    def line_total(self):
        return self.quantity * self.sell_price


class OrderReview(models.Model):
    order = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='reviews')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews_made')
    decision = models.CharField(max_length=20, choices=[('APPROVE','Approve'),('DECLINE','Decline')])
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class OrderFinalization(models.Model):
    order = models.OneToOneField(OrderRequest, on_delete=models.CASCADE, related_name='finalization')
    accountant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='finalizations')
    finalized_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    adjustments = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class PackagingTask(models.Model):
    order = models.OneToOneField(OrderRequest, on_delete=models.CASCADE, related_name='packaging')
    warehouse_worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='packaging_tasks')
    packed_at = models.DateTimeField(null=True, blank=True)
    ready_for_shipment = models.BooleanField(default=False)


class ReturnRequest(models.Model):
    order = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='return_requests')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    salesman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='salesman_returns')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, default='SUBMITTED')


class ReturnAssessment(models.Model):
    return_request = models.OneToOneField(ReturnRequest, on_delete=models.CASCADE, related_name='assessment')
    warehouse_worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assessments')
    condition_notes = models.TextField(blank=True)
    restock_decision = models.BooleanField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class ReturnApproval(models.Model):
    return_request = models.OneToOneField(ReturnRequest, on_delete=models.CASCADE, related_name='approval')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='return_approvals')
    approved = models.BooleanField()
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
