from django.conf import settings
from django.db import models


class Notification(models.Model):
    """An event addressed to one user.

    This is the event feed, not the work queue. What is *waiting* for a role
    is derived from order status (see orders.views.InboxView) so it cannot
    drift; these rows drive the unread badge and the salesman's updates, and
    give later non-order events (bills, vouchers, stock) somewhere to live.
    """

    class Kind(models.TextChoices):
        ORDER_SUBMITTED = 'ORDER_SUBMITTED', 'Order submitted'
        ORDER_APPROVED = 'ORDER_APPROVED', 'Order approved'
        ORDER_REJECTED = 'ORDER_REJECTED', 'Order rejected'
        CUSTOMER_SUBMITTED = 'CUSTOMER_SUBMITTED', 'Customer submitted'
        CUSTOMER_APPROVED = 'CUSTOMER_APPROVED', 'Customer approved'
        CUSTOMER_REJECTED = 'CUSTOMER_REJECTED', 'Customer rejected'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=40, choices=Kind.choices)
    # Generic target so bills, vouchers and stock events slot in later
    # without a schema change.
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.kind} -> {self.recipient_id}"
