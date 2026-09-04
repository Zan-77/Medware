"""Query-parameter filtering for the list endpoints the frontend calls.

The frontend expresses "give me the children of X" as a query parameter -
`/api/inventory/bill-lines/?bill=3`, `/api/products/suppliers/?id=7`. DRF
ignores query parameters a view was never told about, so those requests used
to return the whole table: asking for one bill's lines handed back every line
of every bill.

`django-filter` is deliberately not a dependency here (it is not installed and
these are all plain foreign-key/id lookups), so views declare the parameters
they honour and call `filter_by_query_params` from `get_queryset` - the same
shape as the `get_queryset` scoping already used in `orders` and `website`.
"""

from rest_framework.exceptions import ValidationError


def filter_by_query_params(queryset, request, allowed):
    """Narrow `queryset` by whichever of `allowed` the request actually sent.

    `allowed` maps a query-parameter name to the model field it filters on
    (e.g. `{'bill': 'bill_id'}`). Parameters that are absent or empty are
    ignored; anything else is validated as an integer id so a typo fails with
    a 400 instead of silently returning every row.
    """
    for param, field in allowed.items():
        raw = request.query_params.get(param)
        if raw is None or raw == '':
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise ValidationError({param: f"Expected a numeric id, got '{raw}'."})
        queryset = queryset.filter(**{field: value})
    return queryset
