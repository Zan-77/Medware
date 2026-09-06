"""A voucher is a payment from a customer, not a line on one order.

Adds the number and customer the finance panel asks for, makes the date
settable (it was auto_now_add, so the date on the paper could never be
recorded) and makes `order` optional, since a payment usually settles part of
a running balance rather than one invoice.

Written by hand rather than generated so the two new required columns arrive
nullable, get checked, and only then become required - the safe order for a
table that might not be empty everywhere.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def refuse_incomplete_rows(apps, schema_editor):
    """Stop rather than invent data.

    Every voucher now needs a customer and a unique number, and there is no
    way to infer either for a row written before this migration. On the
    development database this table is empty and the check passes silently;
    anywhere it is not, failing loudly beats guessing.
    """
    Voucher = apps.get_model('finance', 'Voucher')
    stranded = Voucher.objects.filter(customer__isnull=True).count()
    if stranded:
        raise RuntimeError(
            f'{stranded} voucher(s) predate the customer column and cannot be '
            'assigned one automatically. Set finance_voucher.customer_id and '
            'finance_voucher.number for those rows, then re-run migrate.')


def noop(apps, schema_editor):
    """Reversing only drops the columns again; nothing to undo here."""


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_alter_customerbalance_customer'),
        ('customers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='number',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='voucher',
            name='customer',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='vouchers',
                to='customers.customer',
            ),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='order',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vouchers',
                to='orders.orderrequest',
            ),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='date',
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
        migrations.RunPython(refuse_incomplete_rows, noop),
        migrations.AlterField(
            model_name='voucher',
            name='customer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='vouchers',
                to='customers.customer',
            ),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='number',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterModelOptions(
            name='voucher',
            options={'ordering': ['-date', '-id']},
        ),
    ]
