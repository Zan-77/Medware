# Orders: creation and manager approval — design

**Status:** approved in brainstorming, 2026-09-04
**Slice:** order authoring, the manager approval workflow, notifications, and the handoff to the accountant. Finance itself is out of scope.

## Goal

A salesman or manager composes an order for a customer. It arrives in the manager's queue as a request. The manager may adjust quantities, then approves or rejects it with a reason. An approved order becomes visible to the accountant; a rejected one notifies its author. No money moves in this slice.

## Why this shape

Two problems drove the design.

`OrderRequest.status` is a bare `CharField(default='PENDING')` with no choices, and it is listed in `OrderRequestSerializer.fields`. A salesman can `PATCH` their own order to `APPROVED` today. The state machine below is the fix, not decoration.

Internally a customer is a business record, not a login. `OrderRequest.customer` currently points at `User`, which would force a login account for every shop the company sells to. It repoints at a new `Customer` model.

## Decisions taken

| Decision | Choice | Reasoning |
|---|---|---|
| Manager creates an order | Auto-approved, but a real `OrderReview` row is still written naming them as reviewer | Keeps the invariant *every order reaching the accountant has exactly one review row*, so no downstream screen or report needs a special case |
| Customer identity | Standalone `Customer` model in a new `customers` app, with a nullable `OneToOne` to `User` | Internal customers are data (`user IS NULL`); website customers are the same row with a login attached. One record either way — no duplicate customer data |
| Notifications | A real `Notification` table | Chosen for future non-order events (bills, vouchers, stock). See "Two mechanisms" below for how it coexists with the derived queue |
| Order item edits | Allowed while `PENDING`, by the author or any manager; frozen on approve or reject | The manager adjusts quantities as part of reviewing. Freezing at the transition stops edits landing underneath an approval |
| Unit price | Copied from the product on add, then editable; stored per line | A later change to `Product.retail_price` must not silently restate a historical order's value |
| Balances on the order | `previous_balance` and `new_balance` snapshotted at approval | Computed live, reopening an old order would show today's balance rather than the one the customer agreed to |
| Default landing | Products page, pinned first in the nav, for every internal role | Replaces the current `/app/supplier/bills` landing |
| Customer management UI | Django admin only for now | The in-app customer page ships with the e-commerce website. **Limitation: until then only a staff account can add customers; a salesman cannot create one in the field.** |

## Scope

**In:** the `customers` app; the `notifications` app; the order state machine and its transition endpoints; nested order creation; the role-scoped Requests inbox; the orders frontend (list, create, detail, requests); Products as landing page.

**Out:** the accountant's finalize action and any balance mutation; vouchers and payments; warehouse packaging; returns; the in-app customer page; real-time push (polling only — no Channels, no Redis, no ASGI change).

The accountant and warehouse rows in the inbox are defined below and will return empty until the finance slice lands. They are specified now so that slice adds rows rather than reshaping the endpoint.

## Data model

### New app: `customers`

```python
class Customer(models.Model):
    name    = models.CharField(max_length=200)
    phone   = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes   = models.TextField(blank=True)
    # Set only when this customer also holds a website login. NULL for the
    # internal data-log customers that salesmen sell to.
    user    = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='customer')
    created_at = models.DateTimeField(auto_now_add=True)
```

Registered in Django admin. `customers` imports nothing from `orders`, `finance` or `website`; those import it. It is a leaf in the dependency graph.

### New app: `notifications`

```python
class Notification(models.Model):
    class Kind(models.TextChoices):
        ORDER_SUBMITTED = 'ORDER_SUBMITTED', 'Order submitted'
        ORDER_APPROVED  = 'ORDER_APPROVED',  'Order approved'
        ORDER_REJECTED  = 'ORDER_REJECTED',  'Order rejected'

    recipient   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='notifications')
    kind        = models.CharField(max_length=40, choices=Kind.choices)
    # Generic target so bills, vouchers and stock events slot in later without
    # a schema change.
    target_type = models.CharField(max_length=100)
    target_id   = models.CharField(max_length=100)
    message     = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    read_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
```

`ORDER_SUBMITTED` fans out to every user with `role='MANAGER'`. `ORDER_APPROVED` and `ORDER_REJECTED` go to the order's salesman, when it has one.

### Changed: `orders`

```python
class OrderRequest(models.Model):
    class Status(models.TextChoices):
        PENDING   = 'PENDING',   'Pending manager review'
        APPROVED  = 'APPROVED',  'Approved - awaiting accountant'
        REJECTED  = 'REJECTED',  'Rejected by manager'
        FINALIZED = 'FINALIZED', 'Finalized by accountant'   # next slice

    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT,
                                 related_name='order_requests')       # was FK(User)
    status   = models.CharField(max_length=30, choices=Status.choices,
                                default=Status.PENDING)
    previous_balance = models.DecimalField(max_digits=12, decimal_places=2,
                                           null=True, blank=True)     # snapshot at approval
    new_balance      = models.DecimalField(max_digits=12, decimal_places=2,
                                           null=True, blank=True)     # snapshot at approval
    # origin, salesman, created_at, notes unchanged

    @property
    def total(self):
        return sum(item.line_total for item in self.items.all())


class OrderItem(models.Model):
    note = models.TextField(blank=True)          # new
    # product, quantity, sell_price, return_quantity unchanged

    @property
    def line_total(self):
        return self.quantity * self.sell_price
```

`customer` uses `PROTECT`: deleting a customer who has orders must fail loudly rather than cascade away their order history.

Totals are properties, never stored columns — a stored total can disagree with its own lines.

**Where the balance snapshots come from.** At approval, `previous_balance` is read from the customer's `finance.CustomerBalance.outstanding_balance`, or `0` when no balance row exists yet, and `new_balance = previous_balance + order.total`. This slice **reads** `CustomerBalance` and never writes it — moving the customer's actual balance is the accountant's finalize step, which belongs to the finance slice. So an approved order records what the balance *would become*, while the customer's real balance stays untouched until finance lands. That is intentional, and it is the one place where the snapshot and the live balance are expected to disagree.

### Changed: `finance`

`CustomerBalance.customer` repoints from `User` to `customers.Customer`.

### Migration note

`OrderRequest`, `OrderItem`, `CustomerBalance` and customer-role `User` rows are all **empty** (verified 2026-09-04). The foreign-key repointing needs no data migration, no backfill and no compatibility shim. This is only true while those tables stay empty.

## State machine

| From | Action | Actor | To | Side effects (one transaction) |
|---|---|---|---|---|
| — | create | Salesman, Manager | `PENDING` | order + items; `ORDER_SUBMITTED` to all managers |
| `PENDING` | approve | Manager | `APPROVED` | `OrderReview(APPROVE)`; balance snapshots; `RequestTransition`; `ORDER_APPROVED` to salesman |
| `PENDING` | reject | Manager | `REJECTED` | `OrderReview(DECLINE, notes)`; `RequestTransition`; `ORDER_REJECTED` to salesman |
| `APPROVED` | finalize | Accountant | `FINALIZED` | **next slice** |

A manager creating an order runs create then approve in the same transaction, so the order is born `APPROVED` with its review row present.

Every transition writes an `audit.RequestTransition` row — the model already exists with exactly the needed fields (`source_model`, `source_id`, `from_status`, `to_status`, `actor`, `actor_role`, `notes`).

Any transition attempted from a state not listed above returns **409 Conflict**. Approving an already-approved order is a conflict, not a silent no-op — a double-submitting UI must be told.

## API

### Server-controlled fields

`status`, `origin`, `salesman`, `previous_balance` and `new_balance` are **read-only in the serializer**. `origin` derives from the creator's role; `salesman` is the requesting user when they hold that role. `status` moves only through the action endpoints below.

### Endpoints

```
POST   /api/orders/order-requests/              create, nested items, atomic
GET    /api/orders/order-requests/              list, scoped, ?status= ?customer=
GET    /api/orders/order-requests/<id>/         detail: items, totals, names
PATCH  /api/orders/order-requests/<id>/         PENDING only; author or manager
POST   /api/orders/order-requests/<id>/approve/ Manager
POST   /api/orders/order-requests/<id>/reject/  Manager, {"notes": required}
GET    /api/orders/inbox/                       role-scoped work queue
GET    /api/notifications/          ?unread=true recipient == request.user only
POST   /api/notifications/<id>/read/            marks read
GET    /api/customers/                          Manager, Accountant, Salesman
```

`reject` with missing or blank `notes` returns **400**. A rejection can never reach a salesman without a reason.

List filtering reuses `mysite.filters.filter_by_query_params`, so `?status=` and `?customer=` behave like every other list endpoint in the project.

### Doors being closed

`OrderReviewViewSet` currently accepts `POST` from a manager, and `OrderItemViewSet` accepts `POST` from anyone with access. Both walk around the state machine — the second would let a line be added to an order *after* approval, changing the value beneath it.

- Reviews become read-only over the API; they are created only by `approve` and `reject`.
- Order items are writable only while the parent order is `PENDING`, and only by its author or a manager. Otherwise **409**.

### Permissions

| Endpoint | Manager | Accountant | Salesman | Warehouse | Customer |
|---|---|---|---|---|---|
| create order | ✅ | ❌ | ✅ | ❌ | ❌ |
| list / detail | all | all | own only | all | ❌ |
| edit while pending | ✅ any | ❌ | ✅ own | ❌ | ❌ |
| approve / reject | ✅ | ❌ | ❌ | ❌ | ❌ |
| inbox | ✅ | ✅ | ✅ | ✅ | ❌ |

Salesman scoping reuses the existing `orders.views.scope_to_user`.

### The inbox, and why there are two mechanisms

`GET /api/orders/inbox/` returns what is waiting for the requesting user:

| Role | Rows |
|---|---|
| Manager | orders `PENDING` |
| Accountant | orders `APPROVED` (empty until finance) |
| Warehouse | orders `FINALIZED` (empty until finance) |
| Salesman | their unread `ORDER_REJECTED` notifications |

For the queue roles the inbox is **derived from order status**. An order sits in the manager's queue because it *is* pending, not because a row somewhere says so — so the queue cannot drift. A notification table used as the queue can drift in both directions: a pending order with no row is work that silently vanishes, and a row for an already-approved order is phantom work that never clears.

The `Notification` table is the **event feed**: it drives the unread badge, the salesman's updates, and every future non-order alert. The queue is state; the feed is events. Both are deliberate.

## Frontend

New `features/orders`, following the existing feature layout (`*.routes.ts`, `services/`, `types/`, `pages/`).

| Route | Page |
|---|---|
| `/app/orders` | list, role-scoped |
| `/app/orders/new` | create |
| `/app/orders/:orderId` | detail, with approve/reject for managers |
| `/app/requests` | the inbox |

**Navigation.** `الطلبات` becomes functional — its dropdown currently holds two copy-pasted inventory links. Products is pinned first and becomes the post-login landing for every internal role, replacing `/app/supplier/bills` in `LoginPage` and `registerWizard/Step2`. A **Requests** entry carries an unread badge, polled with TanStack Query's `refetchInterval`.

**The line-items editor is the one genuinely new component.** Every form in the app today edits a single flat entity; nothing has repeating rows. It uses `useFieldArray` from react-hook-form, with `ControlledSearchSelectInput` for the customer and for each row's product, and `ControlledInput` for quantity, note and unit price. Choosing a product prefills `sell_price` from its retail price, editable thereafter.

**Totals display live as the user types, but the server's response is authoritative.** The client recomputes for feedback only; a saved order always shows the server's numbers. Otherwise a JS float and a Postgres `DECIMAL` can round differently, showing one figure and storing another.

**Types mirror the serializers exactly** — foreign keys are named after the model field (`customer`, `product`), not with an `Id` suffix, and read-only labels arrive as `*_name`. This is the convention the inventory and products types were corrected to.

`Permissions.tsx` gains real per-role `orders` entries. Its existing `orders` key is declared `dataType: Suppliers`, a copy-paste slip to fix while there.

All strings go through `t(...)` with keys added to `src/i18n/ar.ts`.

## Testing

The backend has a working Django test suite (49 tests) and is where the invariants live. The frontend has no test runner and none is being added; its gate is `tsc -b` and `npm run build`.

Backend tests, each asserting real behaviour through the API:

- Salesman creates an order → `PENDING`, items attached, total correct, managers notified.
- Manager creates an order → `APPROVED` with exactly one `OrderReview` naming them.
- `PATCH {"status": "APPROVED"}` by a salesman on their own order → status unchanged. *This is the regression test for the current hole.*
- Approve by a salesman or accountant → 403. By a manager → 200, review row, transition row, notification.
- Reject with blank notes → 400. With notes → 200, salesman notified, reason retrievable.
- Approve an already-approved order → 409.
- Add an item to an `APPROVED` order → 409. To a `PENDING` order as its author or a manager → 201.
- Balance snapshots frozen at approval do not move when the customer's balance later changes.
- Inbox returns pending orders for a manager, only their own rejections for a salesman, empty for an accountant in this slice.
- A notification list returns only the requesting user's rows.
- Deleting a customer who has orders → `ProtectedError`, not a cascade.

## Build order

Backend before frontend, and the state machine before anything reads it. Three screens built against a status field with no rules produce orders in impossible states that no amount of frontend work repairs.

1. `customers` app, model, admin, repointed foreign keys, migrations.
2. Order state machine: status choices, read-only serializer fields, `approve`/`reject` actions, audit and review writes, the closed doors.
3. `notifications` app plus the fan-out on each transition.
4. The inbox endpoint.
5. Frontend: services and types, then list and detail, then the create form, then the Requests tab and navigation changes.

Each backend step is independently testable and lands with its tests. The frontend cannot begin before step 2 is green.
