# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = "MANAGER", "Manager"
        ACCOUNTANT = "ACCOUNTANT", "Accountant"
        SALESMAN = "SALESMAN", "Salesman"
        CUSTOMER = "CUSTOMER", "Customer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"