# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        GUEST = "guest", "Guest"
        MANAGER = "manager", "Manager"
        ACCOUNTANT = "accountent", "Accountant"
        SALESMAN = "salesman", "Salesman"
        WAREHOUSE_WORKER = "warehouse_worker", "Warehouse Worker"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.GUEST,
    )

    # For website customer verification flow
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"