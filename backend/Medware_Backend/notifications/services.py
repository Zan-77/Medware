from django.contrib.auth import get_user_model
from django.utils import timezone

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


def resolve(kind, target):
    """Mark "this needs your attention" notifications for `target` as read.

    A `..._SUBMITTED` row is a standing request for a decision. Once the
    decision is made the row is answered, but nothing used to say so, so the
    unread badge kept counting work that no longer existed - approve both
    pending orders and it still read 2.

    Cleared for every recipient, not just the actor: the order is no longer
    waiting on any manager once one of them has ruled on it.
    """
    return (Notification.objects
            .filter(kind=kind,
                    target_type=type(target).__name__,
                    target_id=str(target.pk),
                    read_at__isnull=True)
            .update(read_at=timezone.now()))
