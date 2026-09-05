from django.db import migrations


def verify_existing_accounts(apps, schema_editor):
    """Every account that exists at this point predates the approval gate.

    Without this, switching enforcement on leaves the only accounts in the
    database - both managers, both unverified, with no superuser - locked out
    of everything, recoverable only through a Django shell.
    """
    User = apps.get_model('users', 'User')
    User.objects.all().update(is_verified=True)


def noop(apps, schema_editor):
    """Irreversible by design: we cannot tell which rows were unverified."""


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_options_user_users_user_unique_email_ci'),
    ]

    operations = [
        migrations.RunPython(verify_existing_accounts, noop),
    ]
