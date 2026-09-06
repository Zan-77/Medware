import threading

from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from products.models import Product

from .models import InventoryCategory, InventoryItem, StockEntry, SupplierBillLine

# Product and InventoryItem mirror each other, so each sync would trigger the
# other. Creating a catalogue entry for a directly-added inventory item fires
# sync_product_to_inventory, which cannot see the link yet and would create a
# SECOND inventory item. This flag makes that round trip a no-op.
_sync_state = threading.local()


def _syncing():
    return getattr(_sync_state, 'active', False)


@receiver(post_save, sender=Product)
def sync_product_to_inventory(sender, instance, **kwargs):
    if _syncing():
        return

    category, _ = InventoryCategory.objects.get_or_create(name='Uncategorized')
    item = InventoryItem.objects.filter(product=instance).first()
    if item is None:
        item = InventoryItem(product=instance, category=category)

    item.name = instance.name
    item.whole_price = instance.whole_price
    item.retail_price = instance.retail_price
    item.image_url = instance.image_url
    item.save()


@receiver(post_save, sender=InventoryItem)
def sync_inventory_item_to_product(sender, instance, **kwargs):
    """An item added straight to inventory still needs a catalogue entry.

    Orders reference products, not inventory items, so before this an
    inventory-only item could not be ordered at all: the order form had no
    valid product id to send and the request failed.

    Both branches use queryset.update(), which bypasses post_save - that is
    what keeps the two syncs from bouncing off each other.
    """
    if _syncing():
        return

    if instance.product_id:
        # Keep the catalogue entry in step when the item is edited, so the two
        # cannot drift apart after they are linked.
        Product.objects.filter(pk=instance.product_id).update(
            name=instance.name,
            whole_price=instance.whole_price,
            retail_price=instance.retail_price,
            image_url=instance.image_url,
        )
        return

    _sync_state.active = True
    try:
        product = Product.objects.create(
            name=instance.name,
            whole_price=instance.whole_price,
            retail_price=instance.retail_price,
            image_url=instance.image_url,
        )
    finally:
        _sync_state.active = False

    InventoryItem.objects.filter(pk=instance.pk).update(product=product)
    instance.product = product


@receiver(post_save, sender=SupplierBillLine)
def create_receipt_for_supplier_line(sender, instance, created, **kwargs):
    if instance.item_id:
        category = instance.category
        if category is None:
            category, _ = InventoryCategory.objects.get_or_create(name='Uncategorized')
        if instance.item.category_id != category.id:
            InventoryItem.objects.filter(pk=instance.item_id).update(category_id=category.id)

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