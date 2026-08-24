from django.db import models
from django.conf import settings
from products.models import ProductSupplier


class InventoryCategory(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True, null=True)
    whole_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class SupplierBill(models.Model):
    supplier = models.ForeignKey(ProductSupplier, on_delete=models.CASCADE, related_name='inventory_bills')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='supplier_bills')
    date = models.DateField()
    notes = models.TextField(blank=True)


class SupplierBillLine(models.Model):
    bill = models.ForeignKey(SupplierBill, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


class StockEntry(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='stock_entries')
    quantity = models.IntegerField()
    expiry_date = models.DateField(null=True, blank=True)
    source_bill_line = models.ForeignKey(SupplierBillLine, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    movement_type = models.CharField(max_length=20, choices=[('RECEIPT','Receipt'),('RETURN','Return'),('ADJUSTMENT','Adjustment')], default='RECEIPT')

