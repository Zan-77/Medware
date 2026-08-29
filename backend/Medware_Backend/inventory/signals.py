from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from products.models import Product

from .models import InventoryCategory, InventoryItem, StockEntry, SupplierBillLine


@receiver(post_save, sender=Product)
def sync_product_to_inventory(sender, instance, **kwargs):
    category, _ = InventoryCategory.objects.get_or_create(name='Uncategorized')
    item = InventoryItem.objects.filter(product=instance).first()
    if item is None:
        item = InventoryItem(product=instance, category=category)

    item.name = instance.name
    item.whole_price = instance.whole_price
    item.retail_price = instance.retail_price
    item.image_url = instance.image_url
    item.save()


@receiver(post_save, sender=SupplierBillLine)
def create_receipt_for_supplier_line(sender, instance, created, **kwargs):
    receipt = StockEntry.objects.filter(source_bill_line=instance).first()
    if not instance.item_id:
        if receipt:
            receipt.delete()
        return

    StockEntry.objects.update_or_create(
        source_bill_line=instance,
        defaults={
            'item': instance.item,
            'quantity': instance.quantity,
            'expiry_date': instance.expiry_date,
            'movement_type': 'RECEIPT',
        },
    )


@receiver(pre_delete, sender=SupplierBillLine)
def remove_receipt_for_supplier_line(sender, instance, **kwargs):
    StockEntry.objects.filter(source_bill_line_id=instance.pk).delete()