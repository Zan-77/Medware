from django.conf import settings
from django.db import models


class Customer(models.Model):
    """A business the company sells to.

    Internally a customer is data, not a login - salesmen visit shops that
    will never sign in. `user` is filled only when the same customer also
    holds a website account, so a data-log customer gains a login instead of
    becoming a second record.
    """

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending manager approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected by manager'

    # A salesman's customer arrives as a request; a manager's is born approved.
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers_created',
    )
    rejection_notes = models.TextField(blank=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
