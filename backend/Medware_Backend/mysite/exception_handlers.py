"""Project-wide DRF exception handling."""

from django.db.models.deletion import ProtectedError, RestrictedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """Turn delete-integrity errors into 409 instead of a 500.

    Several models are intentionally referenced with on_delete=PROTECT (e.g.
    OrderItem.product). Deleting a referenced row raises ProtectedError, which
    DRF does not know about, so it escaped as an unhandled 500. It is a client
    error - the row is in use - so report it as 409 Conflict.
    """
    if isinstance(exc, (ProtectedError, RestrictedError)):
        referencing = getattr(exc, 'protected_objects', None) or getattr(exc, 'restricted_objects', None) or []
        return Response(
            {
                'detail': 'This record is referenced by other records and cannot be deleted.',
                'referenced_by': sorted({type(obj).__name__ for obj in referencing}),
            },
            status=status.HTTP_409_CONFLICT,
        )

    return drf_exception_handler(exc, context)
