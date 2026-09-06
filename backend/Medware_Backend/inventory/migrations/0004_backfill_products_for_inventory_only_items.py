from django.db import migrations


def create_products_for_inventory_only_items(apps, schema_editor):
    """Give every inventory item a catalogue entry.

    Until now the sync ran one way only: saving a Product created an
    InventoryItem, but an item added straight to inventory got no Product. And
    orders reference products, so those items could not be ordered at all - the
    order form had no valid product id to send and the request failed.

    This is additive. Nothing existing is modified except the previously empty
    `product` link on the orphaned items themselves.
    """
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    Product = apps.get_model('products', 'Product')

    for item in InventoryItem.objects.filter(product__isnull=True):
        product = Product.objects.create(
            name=item.name,
            whole_price=item.whole_price,
            retail_price=item.retail_price,
            image_url=item.image_url,
        )
        # update() rather than save(): historical models carry no signals, and
        # this keeps the write to the single column that needs it.
        InventoryItem.objects.filter(pk=item.pk).update(product=product)


def noop(apps, schema_editor):
    """Irreversible by design.

    Deleting the products again would break any order raised against one in the
    meantime, and we cannot tell which catalogue entries came from here.
    """


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_assign_inventory_categories'),
        ('products', '0002_productsupplier_supplier_and_more'),
    ]

    operations = [
        migrations.RunPython(create_products_for_inventory_only_items, noop),
    ]
