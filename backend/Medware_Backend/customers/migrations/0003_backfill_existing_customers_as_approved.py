from django.db import migrations


def approve_existing_customers(apps, schema_editor):
    """Every row that exists at this point predates the approval workflow.

    Those customers were created back when only a manager could add one, so
    they were implicitly approved. Without this they default to PENDING with a
    NULL created_by, which the salesman scoping filter excludes - silently
    hiding customers a salesman could order against the day before.
    """
    Customer = apps.get_model('customers', 'Customer')
    Customer.objects.all().update(status='APPROVED')


def noop(apps, schema_editor):
    """Irreversible by design: we cannot tell which rows were PENDING before."""


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_customer_created_by_customer_rejection_notes_and_more'),
    ]

    operations = [
        migrations.RunPython(approve_existing_customers, noop),
    ]
