from django.contrib import admin
from .models import InventoryCategory, InventoryItem, SupplierBill, SupplierBillLine, StockEntry

admin.site.register(InventoryCategory)
admin.site.register(InventoryItem)
admin.site.register(SupplierBill)
admin.site.register(SupplierBillLine)
admin.site.register(StockEntry)
