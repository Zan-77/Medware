from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierCategory(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supplied_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='suppliers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('supplier', 'category')
        ordering = ['-created_at']
        verbose_name_plural = 'Supplier Categories'

    def __str__(self):
        return f"{self.supplier.name} -> {self.category.name}"


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement (kg, liter, box, etc.)",
        default='unit'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Bill(models.Model):
    class Status(models.TextChoices):
        ORDERED = "ORDERED", "Ordered"
        RECEIVED = "RECEIVED", "Received"

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='bills')
    bill_date = models.DateTimeField()  # Same as received date (no delay)
    bill_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ORDERED,
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='bills_created')
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-bill_date']
        indexes = [
            models.Index(fields=['supplier', '-bill_date']),
            models.Index(fields=['status', '-bill_date']),
        ]

    def __str__(self):
        return f"{self.bill_number} - {self.supplier.name} ({self.bill_date.date()})"

    def calculate_total(self):
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        return total


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='bill_items')
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    batch_number = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=100, blank=True, help_text="Size/variant (e.g., 500g, 1L)")
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['bill', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity} {self.product.unit} (Bill: {self.bill.bill_number})"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal('0.000'),
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    last_restocked = models.DateTimeField(blank=True, null=True)
    reorder_level = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('10.000'),
        validators=[MinValueValidator(Decimal('0.000'))]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Inventory'

    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.product.unit}"

