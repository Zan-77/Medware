from django.contrib.auth import get_user_model

from .models import Notification


def managers():
    """Every manager - the recipients of a new order request."""
    return get_user_model().objects.filter(role='MANAGER')


def notify(recipients, kind, target, message=''):
    """Create one notification per recipient, pointing at `target`.

    `recipients` may be empty - a manager-created order has no salesman to
    notify - so callers never need to guard.
    """
    rows = [
        Notification(
            recipient=recipient,
            kind=kind,
            target_type=type(target).__name__,
            target_id=str(target.pk),
            message=message,
        )
        for recipient in recipients
    ]
    return Notification.objects.bulk_create(rows)
