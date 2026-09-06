from django.db import migrations


def assign_inventory_categories(apps, schema_editor):
    InventoryCategory = apps.get_model('inventory', 'InventoryCategory')
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    SupplierBillLine = apps.get_model('inventory', 'SupplierBillLine')

    uncategorized, _ = InventoryCategory.objects.get_or_create(name='Uncategorized')

    for item in InventoryItem.objects.all():
        latest_line = (
            SupplierBillLine.objects
            .filter(item_id=item.pk, category__isnull=False)
            .select_related('bill')
            .order_by('-bill__date', '-pk')
            .first()
        )
        category_id = latest_line.category_id if latest_line else uncategorized.pk
        InventoryItem.objects.filter(pk=item.pk).update(category_id=category_id)


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0002_alter_supplierbill_supplier'),
    ]

    operations = [
        migrations.RunPython(assign_inventory_categories, migrations.RunPython.noop),
    ]