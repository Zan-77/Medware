from django.db import models
from products.models import Product
from users.models import User


class OrderRequest(models.Model):
    ORIGIN_CHOICES = [
        ('SALESMAN', 'Salesman'),
        ('MANAGER', 'Manager'),
        ('CUSTOMER', 'Customer'),
    ]
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    # A customer is a business record, not a login - see customers.Customer.
    # PROTECT because deleting a customer must never cascade away their
    # order history.
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='order_requests')
    salesman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='salesman_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, default='PENDING')

    def __str__(self):
        return f"OrderRequest {self.id} ({self.status})"


class OrderItem(models.Model):
    order_request = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    return_quantity = models.IntegerField(default=0)


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
