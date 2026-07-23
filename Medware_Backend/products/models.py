from django.db import models

from users.models import User

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

class Bill(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='bills')
    date = models.DateField()

    def __str__(self):
        return f"Bill {self.id} - {self.supplier.name}"

class Archive(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archives_as_customer', null=True, blank=True)
    salesman = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archives_as_salesman', null=True, blank=True)

    def __str__(self):
        return f"Archive {self.id}"

class Order(models.Model):
    archive = models.ForeignKey(Archive, on_delete=models.CASCADE, related_name='orders')
    date = models.DateField()
    packaging_date = models.DateField(null=True, blank=True)
    recieve_date = models.DateField(null=True, blank=True)
    salesman_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    return_quantity = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Order {self.order.id}"

class ProductSupplier(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='product_suppliers')
    category = models.CharField(max_length=50)
    quantity = models.IntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - Bill {self.bill.id}"

class Voucher(models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    salesman_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Voucher {self.id}"

class OrderVoucher(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_vouchers')
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)

    def __str__(self):
        return f"Order {self.order.id} - Voucher {self.voucher.id}"
