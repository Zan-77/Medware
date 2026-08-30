# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = "GUEST", "Guest"
        MANAGER = "MANAGER", "Manager"
        ACCOUNTANT = "ACCOUNTANT", "Accountant"
        SALESMAN = "SALESMAN", "Salesman"
        WAREHOUSE_WORKER = "WAREHOUSE_WORKER", "Warehouse Worker"
        CUSTOMER = "CUSTOMER", "Customer"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.GUEST,
    )

    # For website customer verification flow
    is_verified = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # Login looks accounts up with `email__iexact`, so uniqueness has
            # to be case-insensitive to actually guarantee a single match -
            # a plain unique=True would still allow A@x.com and a@x.com.
            # Blank emails are excluded: AbstractUser defaults email to '' and
            # accounts may legitimately be created without one.
            models.UniqueConstraint(
                Lower('email'),
                condition=~models.Q(email=''),
                name='users_user_unique_email_ci',
            ),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"