from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    whole_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    name = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name

class ProductSupplier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - Bill {self.bill.id}"
