from django.db import models
from django.conf import settings


class Voucher(models.Model):
    order = models.ForeignKey('orders.OrderRequest', on_delete=models.CASCADE, related_name='vouchers')
    salesman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='vouchers')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    reference = models.CharField(max_length=200, blank=True)


class PaymentRecord(models.Model):
    order = models.ForeignKey('orders.OrderRequest', on_delete=models.CASCADE, related_name='payments')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments_recorded')
    date = models.DateTimeField(auto_now_add=True)


class CommissionRecord(models.Model):
    order = models.ForeignKey('orders.OrderRequest', on_delete=models.CASCADE, related_name='commissions')
    salesman = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='commissions')
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    earned_amount = models.DecimalField(max_digits=12, decimal_places=2)
    adjusted_for_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)


class CustomerBalance(models.Model):
    customer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='balance')
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

