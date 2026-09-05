# Customers, finance panel, navigation and inventory details — design

**Status:** approved in brainstorming, 2026-09-05
**Covers:** customer creation with manager approval, a role badge, the navigation restructure, the finance panel, product category filtering, and inventory item details.

## Why

Two sessions of work produced almost nothing a user can see: the orders slice was four-fifths backend, and the only new screens were Orders and Requests. Worse, orders require a customer and the customer UI was deferred — so **no order can be raised through the app at all**. That is the first thing this fixes.

Everything else here is a screen over an API that already exists and is already role-gated. The finance backend in particular is complete and mounted at `/api/finance/` with no front end whatsoever, which is why "finance is still not working".

## Decisions taken

| Decision | Choice | Reasoning |
|---|---|---|
| Who creates customers | Salesman **and** manager | The salesman meets the customer; a salesman who cannot add one cannot raise an order |
| Salesman-created customers | Become an approval **request** to the manager | The user's call. Mirrors the order workflow exactly, so it reuses the state machine, the audit log, the notifications and the Requests inbox rather than inventing a second pattern |
| Manager-created customers | Born `APPROVED`, with an audit row naming the manager | Same shape as the order decision: no downstream screen needs a special case for "approved by nobody" |
| Customer approval audit | `audit.RequestTransition`, not a new review model | It is already generic (`source_model`, `source_id`, `from_status`, `to_status`, `actor`, `actor_role`, `notes`). A `CustomerReview` model would duplicate it |
| Orders for a pending customer | Refused with 400 until the customer is approved | An order approved against a customer the company has not accepted is a record nobody can act on. The manager sees the customer request in the same inbox, so the wait is short |
| Home / Employees / Settings | Rendered greyed and non-navigable | The user's choice (b). They have no backend at all — `users/urls.py` exposes role-check viewsets, not a staff directory |
| Suppliers and Purchases | **Unchanged** | The user's explicit instruction. The existing Suppliers dropdown and its bills entry keep their current structure and labels |
| Product categories | Filter through `inventory_item__category`; no schema change | `Product` has no category field, but `inventory/signals.py` auto-creates a linked `InventoryItem` per product and that carries the category |
| Role badge source | `authSlice.user.role`, already decoded from the JWT | `users/serializers.py` sets `refresh['role'] = user.role` and the frontend already stores it. No API change |

## Security note — recorded, not changed

The registration approval gate is deliberately **disabled** in this build: `validate_role` and all three `is_verified` hooks sit commented in `users/serializers.py`. A self-registered `MANAGER` is a real manager immediately. This is intentional for development and nothing here touches it. It does mean every role in this spec can be exercised locally without a seeded account.

## Scope

**In:** the customer approval workflow and its screens; the role badge; the navigation restructure; the finance panel's four read/write screens; product category filtering; inventory item details.

**Out:** the accountant's order-finalisation step and any movement of `CustomerBalance` (still the finance slice proper — this gives the accountant screens to *see* finance, not to complete an order's lifecycle); Home, Employees and Settings beyond greyed placeholders; any change to the registration gate; any change to Suppliers or Purchases.

---

## Part A — Customer approval

### Model

```python
class Customer(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'PENDING',  'Pending manager approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected by manager'

    # existing: name, phone, address, notes, user, created_at
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='customers_created')
    rejection_notes = models.TextField(blank=True)
```

`status`, `created_by` and `rejection_notes` are **read-only in the serializer**. `status` moves only through the action endpoints — the same rule that closed the order hole.

### Transitions

| From | Action | Actor | To | Side effects (one transaction) |
|---|---|---|---|---|
| — | create by salesman | Salesman | `PENDING` | `RequestTransition`; `CUSTOMER_SUBMITTED` to every manager |
| — | create by manager | Manager | `APPROVED` | `RequestTransition` naming the manager |
| `PENDING` | approve | Manager | `APPROVED` | `RequestTransition`; `CUSTOMER_APPROVED` to `created_by` |
| `PENDING` | reject (notes required) | Manager | `REJECTED` | `RequestTransition`; `CUSTOMER_REJECTED` to `created_by` |

Approving or rejecting anything not `PENDING` returns **409**. Rejecting with blank `notes` returns **400**. Both actions check `request.user.role == 'MANAGER'` **inside the action** — `RoleMethodPermission` keys off the HTTP method, so a `POST` to `/approve/` passes the class-level check for a salesman.

`Notification.Kind` gains `CUSTOMER_SUBMITTED`, `CUSTOMER_APPROVED`, `CUSTOMER_REJECTED`.

### API

```
GET    /api/customers/                    scoped, ?status=
POST   /api/customers/                    Salesman, Manager
PATCH  /api/customers/<id>/               PENDING only, creator or manager
POST   /api/customers/<id>/approve/       Manager
POST   /api/customers/<id>/reject/        Manager, {"notes": required}
```

**Scoping:** managers and accountants see every customer. A salesman sees approved customers plus their own pending and rejected ones — never another salesman's unapproved record.

**Order creation validates the customer is `APPROVED`**, returning 400 otherwise, so an order can never be raised against a customer the company has not accepted.

### Inbox

`GET /api/orders/inbox/` gains customer rows. This is what its generic row shape was for:

| Role | Existing rows | New rows |
|---|---|---|
| Manager | orders `PENDING` | customers `PENDING` |
| Salesman | unread order rejections | unread customer rejections |

Each row keeps the same shape — `{kind, order, message, notification_id}` — with a sibling `customer` key for customer rows. The frontend switches on `kind`.

---

## Part B — Role badge

A small pill beneath the user's name in the navigation, reading `t(user.role)`. `ar.ts` has `manager` and `guest`; `accountant`, `salesman`, `warehouse_worker` and `customer` get added.

---

## Part C — Navigation

```
Home                    greyed, non-navigable
Requests  ⌈unread badge⌉
── Inventory ──   Inventory · Products
── Inbound ──     Orders · Customers
── Outbound ──    Suppliers · Purchases        (UNCHANGED - existing entries)
── Finance ──     Vouchers · Payments · Balances · Commissions
Employees               greyed, non-navigable
── Preferences ── Settings                     greyed, non-navigable
```

Greyed entries are rendered `disabled` with no `onClick`, so they cannot navigate anywhere. The Finance group is visible only to `MANAGER` and `ACCOUNTANT`; Customers only to roles that may read them.

Requests sits at top level rather than inside a group: it is cross-cutting work, and it carries the unread badge.

---

## Part D — Finance panel

Four screens under `/app/finance/`, for `MANAGER` and `ACCOUNTANT`:

| Route | Screen | API |
|---|---|---|
| `/app/finance/vouchers` | list + create | `/api/finance/vouchers/` |
| `/app/finance/payments` | list + create | `/api/finance/payments/` |
| `/app/finance/balances` | read-only | `/api/finance/balances/` |
| `/app/finance/commissions` | read-only | `/api/finance/commissions/` |

**Backend work required first.** The finance serializers return bare foreign keys, so every table would show `customer: 14` — the exact defect just fixed on the orders screen. Each gains read-only labels: `customer_name`, `salesman_name`, `recorded_by_name`, and an `order` reference. `CustomerBalance.customer` now points at `customers.Customer`, so `customer_name` sources from `customer.name`.

---

## Part E — Products by category, and inventory item details

**Backend:** `ProductViewSet` gains a `?category=` filter through `inventory_item__category`, validated as a numeric id. `ProductSerializer` gains read-only `category` and `category_name`, sourced from `inventory_item.category`. Both are nullable — a product whose inventory item was deleted must still serialise.

**Frontend:** a category dropdown above the products table. Managers already create categories on the existing categories page; nothing new is needed for that.

The `InventoryItemsDetails` stub is currently wired to two different routes. It splits:

| Route | Page |
|---|---|
| `/app/inventory/items` | every inventory item |
| `/app/inventory/categories/:categoryId` | items in one category |
| `/app/inventory/items/:itemId` | **item details** |

Item details shows name, sku, category, whole and retail price, current quantity (the model's `quantity` property), and the stock entries feeding it with their movement type, expiry and source bill line.

---

## Testing

The backend suite is the gate — 107 tests pass today. The frontend has no test runner and none is being added; its gate is `tsc -b` and `npm run build`.

New backend tests:

- A salesman creating a customer produces `PENDING` and notifies every manager.
- A manager creating one produces `APPROVED` with an audit row naming them.
- `PATCH {"status": "APPROVED"}` by a salesman leaves the status untouched.
- Approve by a salesman or accountant → 403; by a manager → 200 with audit row and notification.
- Reject with blank notes → 400; with notes → 200, reason retrievable by the creator.
- Approving an already-approved customer → 409.
- A salesman sees approved customers and their own pending ones, never another salesman's.
- Creating an order against a `PENDING` customer → 400.
- The manager inbox carries pending customers; the salesman inbox carries their unread customer rejections.
- `?category=` narrows the product list; an unknown category id → 400.
- A product serialises `category_name`, and still serialises when it has no inventory item.

## Build order

1. **Customer approval backend** — model, transitions, scoping, order validation, inbox rows.
2. **Customers page + role badge** — the screens that unblock orders.
3. **Navigation restructure** — makes everything new reachable, greys the three placeholders.
4. **Finance serializers + panel** — labels first, then the four screens.
5. **Products by category + inventory item details.**

Backend precedes its screens in every case. Steps 4 and 5 are independent of 1–3 and of each other.
