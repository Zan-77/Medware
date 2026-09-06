"""Clear the request notifications whose decision has already been made.

The badge counts unread notifications, but nothing marked a `..._SUBMITTED`
row read when the order or customer it asked about left its pending state. A
manager who approved both waiting orders still saw "2", permanently.

The code fix stops new rows getting stuck. This settles the ones already
stranded: every submitted-request notification whose target is no longer
pending is marked read, dated now rather than backdated - now is when it was
actually resolved as far as this system can honestly say.

Nothing is deleted, and rows whose target is still pending are left alone.
"""

from django.db import migrations
from django.utils import timezone


def mark_answered_requests_read(apps, schema_editor):
    Notification = apps.get_model('notifications', 'Notification')
    OrderRequest = apps.get_model('orders', 'OrderRequest')
    Customer = apps.get_model('customers', 'Customer')

    now = timezone.now()

    for kind, model, target_type in (
        ('ORDER_SUBMITTED', OrderRequest, 'OrderRequest'),
        ('CUSTOMER_SUBMITTED', Customer, 'Customer'),
    ):
        still_pending = {
            str(pk) for pk in
            model.objects.filter(status='PENDING').values_list('pk', flat=True)
        }
        stale = (Notification.objects
                 .filter(kind=kind, target_type=target_type, read_at__isnull=True)
                 .exclude(target_id__in=still_pending))
        stale.update(read_at=now)


def noop(apps, schema_editor):
    """Irreversible: which rows this marked read is not recoverable, and
    un-reading them would put answered requests back on the badge."""


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_alter_notification_kind'),
        # The migrations that put `status` on each model - the field this
        # reads to decide what is still pending.
        ('orders', '0003_orderitem_note_orderrequest_new_balance_and_more'),
        ('customers', '0003_backfill_existing_customers_as_approved'),
    ]

    operations = [
        migrations.RunPython(mark_answered_requests_read, noop),
    ]
