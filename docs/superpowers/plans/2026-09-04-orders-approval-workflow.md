# Orders: Creation and Manager Approval — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A salesman or manager composes an order for a customer; it enters the manager's queue; the manager adjusts quantities then approves or rejects it with a reason; an approved order becomes visible to the accountant and a rejected one notifies its author.

**Architecture:** Backend first, state machine before any screen. A new `customers` app holds the business customer record that `orders` and `finance` both point at. `OrderRequest.status` becomes a `TextChoices` field that is read-only over the serializer and moves only through dedicated `approve`/`reject` action endpoints, each writing an `OrderReview`, an `audit.RequestTransition` and a `Notification` in one transaction. The Requests inbox derives queue rows from order status so it cannot drift, while the `Notification` table carries the event feed.

**Tech Stack:** Django 6.0.5, DRF 3.17.1, simplejwt 5.2.2, PostgreSQL (psycopg 3). Frontend: React 19, React Router 8, TanStack Query 5, TanStack Table 9, react-hook-form 7, i18next (Arabic only), TypeScript 6, Vite 8.

**Spec:** `docs/superpowers/specs/2026-09-04-orders-approval-workflow-design.md`

## Global Constraints

- Backend lives at `c:/Medware/backend/Medware_Backend`; run `python manage.py …` from there. Frontend lives at `c:/Medware/frontemd/frontend`; run npm/npx from there.
- `c:/Medware/frontemd` is a **separate nested git repo** on branch `frontend`. Frontend commits happen there. Backend commits happen in `c:/Medware` on branch `back`.
- The backend test suite is the gate for every backend task: `python manage.py test` must stay green (49 tests pass before this plan starts).
- **There is no frontend test runner and none is to be added.** The frontend gate is `npx tsc -b` exiting 0 and `npm run build` succeeding.
- `status`, `origin`, `salesman`, `previous_balance`, `new_balance` are **read-only in the serializer**. `status` moves only through the action endpoints.
- Totals are **computed server-side and never accepted from the client**. `OrderRequest.total` and `OrderItem.line_total` are properties, never stored columns.
- Every state transition writes an `audit.RequestTransition` row.
- Rejecting with blank `notes` returns **400**. A transition from a state that does not allow it returns **409**.
- Every user-facing frontend string goes through `t(...)` with the key added to `src/i18n/ar.ts`. A missing key renders the raw English identifier.
- **Keep the existing frontend UI design.** Reuse `Button`, `Model`, `Form`, `Table`, `TableFilter`, `TableSettings`, `DebouncedInput`, `Toast`, `Text`, `ControlledInput`, `ControlledDateInput`, `ControlledSearchSelectInput`, `ControlledTextArea`, `useOpenMenu`, `hasPermission`. Do not introduce a new UI library, a new styling approach, or a new form library.
- Frontend types mirror the serializers exactly: foreign keys are named after the model field (`customer`, `product`), never with an `Id` suffix; read-only labels arrive as `*_name`.
- No store, context, or data-fetching abstraction beyond the existing pattern: pages call service functions, service functions call `ax`.
- Mixed line endings mean git prints `LF will be replaced by CRLF` warnings. Harmless.

---

### Task 1: The `customers` app, and repointing orders and finance at it

**Files:**
- Create: `customers/__init__.py`, `customers/apps.py`, `customers/models.py`, `customers/admin.py`, `customers/serializers.py`, `customers/views.py`, `customers/urls.py`, `customers/migrations/__init__.py`, `customers/tests.py`
- Modify: `mysite/settings.py` (INSTALLED_APPS), `mysite/urls.py`, `orders/models.py`, `finance/models.py`
- Test: `customers/tests.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `customers.models.Customer` with fields `name`, `phone`, `address`, `notes`, `user` (nullable OneToOne to `settings.AUTH_USER_MODEL`, `related_name='customer'`), `created_at`. `orders.OrderRequest.customer` is `FK('customers.Customer', on_delete=PROTECT, related_name='order_requests')`. `finance.CustomerBalance.customer` is `OneToOneField('customers.Customer', related_name='balance')`. Endpoint `GET/POST /api/customers/` and `/api/customers/<id>/`.

- [ ] **Step 1: Write the failing test**

Create `customers/tests.py`:

```python
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from orders.models import OrderRequest
from users.models import User


class CustomerModelTests(TestCase):
    def test_an_internal_customer_has_no_user_account(self):
        """Outside the website a customer is data, not a login."""
        customer = Customer.objects.create(name='Al Noor Pharmacy', phone='0100000000')

        self.assertIsNone(customer.user)

    def test_a_customer_can_be_linked_to_a_website_account_later(self):
        """The website slice attaches a login to an existing record rather
        than creating a second one."""
        customer = Customer.objects.create(name='Al Noor Pharmacy')
        account = User.objects.create_user(username='alnoor', password='pass', role=User.Role.CUSTOMER)

        customer.user = account
        customer.save()

        self.assertEqual(account.customer, customer)

    def test_deleting_a_customer_with_orders_is_refused(self):
        """PROTECT: order history must never cascade away with the customer."""
        customer = Customer.objects.create(name='Al Noor Pharmacy')
        OrderRequest.objects.create(origin='SALESMAN', customer=customer)

        with self.assertRaises(ProtectedError):
            customer.delete()


class CustomerApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='cust_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='cust_slm', password='pass', role=User.Role.SALESMAN)
        self.warehouse = User.objects.create_user(username='cust_wh', password='pass', role=User.Role.WAREHOUSE_WORKER)
        Customer.objects.create(name='Al Noor Pharmacy', phone='0100000000')

    def test_salesman_can_list_customers(self):
        """The order form's customer picker is a salesman-facing screen."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.get('/api/customers/')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_manager_can_create_a_customer(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Customer.objects.filter(name='Dar Al Shifa').exists())

    def test_salesman_cannot_create_a_customer(self):
        """Until the e-commerce slice, customer records are entered by staff."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 403)

    def test_warehouse_worker_cannot_read_customers(self):
        self.client.force_authenticate(user=self.warehouse)

        resp = self.client.get('/api/customers/')

        self.assertEqual(resp.status_code, 403)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/customers/').status_code, 401)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test customers`
Expected: FAIL — `ModuleNotFoundError: No module named 'customers'`.

- [ ] **Step 3: Create the app package**

`customers/__init__.py` — empty file.

`customers/apps.py`:

```python
from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'
```

`customers/migrations/__init__.py` — empty file.

- [ ] **Step 4: Write the model**

`customers/models.py`:

```python
from django.conf import settings
from django.db import models


class Customer(models.Model):
    """A business the company sells to.

    Internally a customer is data, not a login - salesmen visit shops that
    will never sign in. `user` is filled only when the same customer also
    holds a website account, so a data-log customer gains a login instead of
    becoming a second record.
    """

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
```

- [ ] **Step 5: Write the admin, serializer, viewset and urls**

`customers/admin.py` — this is the only way to add customers until the e-commerce slice:

```python
from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'user')
    search_fields = ('name', 'phone')
```

`customers/serializers.py`:

```python
from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'address', 'notes', 'user', 'created_at']
        read_only_fields = ['created_at']
```

`customers/views.py`:

```python
from rest_framework import permissions, viewsets

from mysite.filters import filter_by_query_params
from users.permissions import RoleMethodPermission

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        # Salesmen read the list to pick a customer on the order form, but
        # customer records are entered by staff until the e-commerce slice.
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        'POST': ['MANAGER'],
        'PUT': ['MANAGER'],
        'PATCH': ['MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        return filter_by_query_params(super().get_queryset(), self.request, {'id': 'id'})
```

`customers/urls.py`:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet

router = DefaultRouter()
router.register(r'', CustomerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

- [ ] **Step 6: Register the app and its URLs**

In `mysite/settings.py`, add to `INSTALLED_APPS` immediately after `'users',`:

```python
    'customers',
```

In `mysite/urls.py`, add to `urlpatterns` after the `api/orders/` line:

```python
    path('api/customers/', include('customers.urls')),
```

- [ ] **Step 7: Repoint the foreign keys**

In `orders/models.py`, replace the `customer` field on `OrderRequest`:

```python
    # A customer is a business record, not a login - see customers.Customer.
    # PROTECT because deleting a customer must never cascade away their
    # order history.
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='order_requests')
```

In `finance/models.py`, replace the `customer` field on `CustomerBalance`:

```python
    customer = models.OneToOneField('customers.Customer', on_delete=models.CASCADE, related_name='balance')
```

- [ ] **Step 7b: Fix customer scoping, without breaking returns**

`orders/views.py` has `scope_to_user`, which narrows a queryset to rows the user is a party to. For a `CUSTOMER`-role user it does `queryset.filter(customer=user)`. Once `OrderRequest.customer` is a `Customer`, that comparison is invalid — the path to the user account is now `customer__user`.

**`scope_to_user` is shared with `ReturnRequestViewSet`, whose `customer` field is still a `User`.** Changing the helper's default would break returns. Change the *call sites* instead, leaving the helper alone.

In `OrderRequestViewSet`:

```python
    def get_queryset(self):
        # OrderRequest.customer is now a Customer record; the path to the
        # account that may read it is customer__user. ReturnRequest still
        # points straight at User, which is why this is set per call site
        # rather than changed in scope_to_user itself.
        return scope_to_user(super().get_queryset(), self.request.user,
                             customer_field='customer__user')
```

In `OrderItemViewSet`:

```python
    def get_queryset(self):
        # Items are scoped through their parent order request.
        return scope_to_user(
            super().get_queryset(),
            self.request.user,
            customer_field='order_request__customer__user',
            salesman_field='order_request__salesman',
        )
```

`ReturnRequestViewSet.get_queryset` is left exactly as it is.

- [ ] **Step 7c: Repair the cross-tenant security test**

`users/tests_security.py:109` builds an order with a `User` as its customer. It is the F8 regression test for cross-tenant order access and must keep testing that. Replace the body of `test_customer_cannot_see_another_customers_order` with:

```python
    def test_customer_cannot_see_another_customers_order(self):
        from customers.models import Customer

        # Both customers now hold a Customer record linked to their account,
        # which is how a website login maps onto a customer.
        mine = Customer.objects.create(name='My shop', user=self.customer)
        theirs = Customer.objects.create(name='Their shop', user=self.other_customer)
        my_order = OrderRequest.objects.create(origin='CUSTOMER', customer=mine, status='PENDING')
        other_order = OrderRequest.objects.create(origin='CUSTOMER', customer=theirs, status='PENDING')
        self.client.force_authenticate(user=self.customer)

        listed = self.client.get('/api/orders/order-requests/')
        self.assertEqual(listed.status_code, 200)
        ids = [row['id'] for row in listed.json()]
        # Positive and negative: seeing my own proves the filter is not simply
        # returning nothing, which would make the assertion below vacuous.
        self.assertIn(my_order.pk, ids)
        self.assertNotIn(other_order.pk, ids)

        detail = self.client.get(f'/api/orders/order-requests/{other_order.pk}/')
        self.assertEqual(detail.status_code, 404)
```

The original asserted only the negative. With scoping now going through `customer__user`, a customer with no `Customer` record would see an empty list and the old assertion would pass without proving anything. The positive assertion closes that.

- [ ] **Step 7d: Update the dev script**

`scripts/method_matrix.py:66` also constructs an `OrderRequest` with a `User`. It is not picked up by Django's test discovery (which matches `test*.py`), so it does not affect the suite, but leave it working:

```python
        from customers.models import Customer
        self.customer_record = Customer.objects.create(name='Matrix customer', user=self.users['CUSTOMER'])
        self.order = OrderRequest.objects.create(
            origin='CUSTOMER', customer=self.customer_record, salesman=self.users['SALESMAN'], status='PENDING')
```

`ReturnRequest.objects.create(... customer=self.users['CUSTOMER'] ...)` on the following lines stays unchanged — returns still point at `User`.

- [ ] **Step 8: Generate and apply migrations**

```bash
python manage.py makemigrations customers orders finance
python manage.py migrate
```

Expected: a new `customers/migrations/0001_initial.py`, plus `AlterField` migrations for `orders` and `finance`. These tables are empty, so no data migration is needed. If Django prompts for a default value, stop — that means a table was not empty and this plan's migration assumption is broken; report it.

- [ ] **Step 9: Run the tests to verify they pass**

Run: `python manage.py test customers`
Expected: 8 tests, all PASS.

- [ ] **Step 10: Run the whole suite**

Run: `python manage.py test`
Expected: OK. Pre-existing tests that construct an `OrderRequest` with a `User` as customer will now fail — fix those call sites to create a `Customer` first. Report any you changed.

- [ ] **Step 11: Commit**

```bash
cd c:/Medware
git add backend/Medware_Backend/customers backend/Medware_Backend/mysite/settings.py backend/Medware_Backend/mysite/urls.py backend/Medware_Backend/orders backend/Medware_Backend/finance
git commit -m "feat: add customers app and repoint orders and finance at it

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Order status becomes a state machine field

Closes the live hole: `status` is currently a free `CharField` listed in the serializer's writable fields, so a salesman can `PATCH` their own order to `APPROVED`.

**Files:**
- Modify: `orders/models.py`, `orders/serializers.py`
- Test: `orders/tests.py`

**Interfaces:**
- Consumes: `customers.models.Customer` from Task 1.
- Produces: `OrderRequest.Status` with members `PENDING`, `APPROVED`, `REJECTED`, `FINALIZED` (values equal to their names). `OrderRequest.total` and `OrderItem.line_total` properties returning `Decimal`. `OrderRequest.previous_balance` / `new_balance` (nullable `DecimalField(max_digits=12, decimal_places=2)`). `OrderItem.note` (`TextField(blank=True)`). `OrderRequestSerializer` exposes `customer_name`, `salesman_name`, `total`, and treats `status`, `origin`, `salesman`, `previous_balance`, `new_balance` as read-only.

- [ ] **Step 1: Write the failing test**

Append to `orders/tests.py`:

```python
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from orders.models import OrderItem, OrderRequest
from products.models import Product
from users.models import User


class OrderStatusFieldTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='st_slm', password='pass', role=User.Role.SALESMAN)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')
        self.order = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman)

    def test_a_new_order_starts_pending(self):
        self.assertEqual(self.order.status, OrderRequest.Status.PENDING)

    def test_order_total_is_the_sum_of_its_lines(self):
        OrderItem.objects.create(order_request=self.order, product=self.product,
                                 quantity=3, sell_price=Decimal('10.50'))
        OrderItem.objects.create(order_request=self.order, product=self.product,
                                 quantity=2, sell_price=Decimal('4.00'))

        self.assertEqual(self.order.total, Decimal('39.50'))

    def test_line_total_is_quantity_times_price(self):
        item = OrderItem.objects.create(order_request=self.order, product=self.product,
                                        quantity=4, sell_price=Decimal('2.25'))

        self.assertEqual(item.line_total, Decimal('9.00'))

    def test_salesman_cannot_patch_their_order_to_approved(self):
        """The regression test for the original hole: `status` was a writable
        free-text field, so a salesman could approve their own order."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.patch(f'/api/orders/order-requests/{self.order.pk}/',
                                 {'status': 'APPROVED'}, format='json')

        self.order.refresh_from_db()
        self.assertIn(resp.status_code, (200, 400))
        self.assertEqual(self.order.status, OrderRequest.Status.PENDING)

    def test_order_detail_carries_readable_names_and_total(self):
        OrderItem.objects.create(order_request=self.order, product=self.product,
                                 quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.salesman)

        row = self.client.get(f'/api/orders/order-requests/{self.order.pk}/').json()

        self.assertEqual(row['customer_name'], 'Al Noor Pharmacy')
        self.assertEqual(row['salesman_name'], 'st_slm')
        self.assertEqual(Decimal(str(row['total'])), Decimal('20.00'))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test orders.tests.OrderStatusFieldTests`
Expected: FAIL — `AttributeError: type object 'OrderRequest' has no attribute 'Status'`.

- [ ] **Step 3: Add the status choices, snapshots, totals and item note**

In `orders/models.py`, replace the `OrderRequest` class body's `status` line and add the rest:

```python
class OrderRequest(models.Model):
    ORIGIN_CHOICES = [
        ('SALESMAN', 'Salesman'),
        ('MANAGER', 'Manager'),
        ('CUSTOMER', 'Customer'),
    ]

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending manager review'
        APPROVED = 'APPROVED', 'Approved - awaiting accountant'
        REJECTED = 'REJECTED', 'Rejected by manager'
        FINALIZED = 'FINALIZED', 'Finalized by accountant'

    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES)
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='order_requests')
    salesman = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='salesman_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    # Frozen when the manager approves. Computed live, reopening an old order
    # would show today's balance rather than the one the customer agreed to.
    previous_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    new_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    @property
    def total(self):
        """Derived, never stored - a stored total can disagree with its lines."""
        return sum((item.line_total for item in self.items.all()), Decimal('0'))

    def __str__(self):
        return f"OrderRequest {self.id} ({self.status})"
```

Add `note` and `line_total` to `OrderItem`:

```python
class OrderItem(models.Model):
    order_request = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    # Copied from the product when the line is added, then editable. A later
    # change to Product.retail_price must not restate a historical order.
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True)
    return_quantity = models.IntegerField(default=0)

    @property
    def line_total(self):
        return self.quantity * self.sell_price
```

Add the import at the top of `orders/models.py`:

```python
from decimal import Decimal
```

- [ ] **Step 4: Make the workflow fields read-only in the serializer**

In `orders/serializers.py`, replace `OrderRequestSerializer`:

```python
class OrderRequestSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default=None)
    salesman_name = serializers.CharField(source='salesman.username', read_only=True, default=None)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderRequest
        fields = [
            'id', 'origin', 'customer', 'customer_name', 'salesman', 'salesman_name',
            'created_at', 'status', 'notes', 'previous_balance', 'new_balance',
            'total', 'items',
        ]
        # `status` moves only through the approve/reject actions. `origin` and
        # `salesman` are derived from the requesting user. Leaving any of them
        # writable lets a salesman approve their own order with a PATCH.
        read_only_fields = ['status', 'origin', 'salesman', 'previous_balance', 'new_balance']
```

- [ ] **Step 5: Generate and apply migrations**

```bash
python manage.py makemigrations orders
python manage.py migrate
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python manage.py test orders.tests.OrderStatusFieldTests`
Expected: 6 tests, all PASS.

- [ ] **Step 7: Run the whole suite and commit**

```bash
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/orders
git commit -m "feat: make order status a state machine field, read-only over the API

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: The `notifications` app

**Files:**
- Create: `notifications/__init__.py`, `notifications/apps.py`, `notifications/models.py`, `notifications/admin.py`, `notifications/serializers.py`, `notifications/services.py`, `notifications/views.py`, `notifications/urls.py`, `notifications/migrations/__init__.py`, `notifications/tests.py`
- Modify: `mysite/settings.py`, `mysite/urls.py`
- Test: `notifications/tests.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `notifications.models.Notification` with `Kind` choices `ORDER_SUBMITTED`, `ORDER_APPROVED`, `ORDER_REJECTED`. `notifications.services.notify(recipients, kind, target, message='')` where `recipients` is an iterable of `User` and `target` is any model instance; it returns the list of created `Notification` rows. `notifications.services.managers()` returns a queryset of all `MANAGER`-role users. Endpoints `GET /api/notifications/` (optional `?unread=true`) and `POST /api/notifications/<id>/read/`.

- [ ] **Step 1: Write the failing test**

Create `notifications/tests.py`:

```python
from django.test import TestCase
from rest_framework.test import APIClient

from customers.models import Customer
from notifications.models import Notification
from notifications.services import managers, notify
from orders.models import OrderRequest
from users.models import User


class NotifyServiceTests(TestCase):
    def setUp(self):
        self.manager_a = User.objects.create_user(username='nt_mgr_a', password='pass', role=User.Role.MANAGER)
        self.manager_b = User.objects.create_user(username='nt_mgr_b', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='nt_slm', password='pass', role=User.Role.SALESMAN)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.order = OrderRequest.objects.create(origin='SALESMAN', customer=self.customer, salesman=self.salesman)

    def test_managers_returns_every_manager_and_nobody_else(self):
        found = set(managers().values_list('username', flat=True))

        self.assertEqual(found, {'nt_mgr_a', 'nt_mgr_b'})

    def test_notify_creates_one_row_per_recipient_pointing_at_the_target(self):
        created = notify(managers(), Notification.Kind.ORDER_SUBMITTED, self.order, message='New order')

        self.assertEqual(len(created), 2)
        row = Notification.objects.get(recipient=self.manager_a)
        self.assertEqual(row.kind, Notification.Kind.ORDER_SUBMITTED)
        self.assertEqual(row.target_type, 'OrderRequest')
        self.assertEqual(row.target_id, str(self.order.pk))
        self.assertIsNone(row.read_at)

    def test_notify_tolerates_an_empty_recipient_list(self):
        """A manager-created order may have no salesman to notify."""
        created = notify([], Notification.Kind.ORDER_APPROVED, self.order)

        self.assertEqual(created, [])
        self.assertEqual(Notification.objects.count(), 0)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='na_slm', password='pass', role=User.Role.SALESMAN)
        self.other = User.objects.create_user(username='na_other', password='pass', role=User.Role.SALESMAN)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.order = OrderRequest.objects.create(origin='SALESMAN', customer=self.customer, salesman=self.salesman)
        self.mine = notify([self.salesman], Notification.Kind.ORDER_REJECTED, self.order, message='Too expensive')[0]
        notify([self.other], Notification.Kind.ORDER_REJECTED, self.order, message='Not yours')

    def test_listing_returns_only_my_notifications(self):
        self.client.force_authenticate(user=self.salesman)

        rows = self.client.get('/api/notifications/').json()

        self.assertEqual([r['id'] for r in rows], [self.mine.pk])
        self.assertEqual(rows[0]['message'], 'Too expensive')

    def test_unread_filter_hides_read_rows(self):
        self.client.force_authenticate(user=self.salesman)
        self.client.post(f'/api/notifications/{self.mine.pk}/read/')

        self.assertEqual(self.client.get('/api/notifications/?unread=true').json(), [])
        self.assertEqual(len(self.client.get('/api/notifications/').json()), 1)

    def test_marking_read_sets_the_timestamp(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/notifications/{self.mine.pk}/read/')

        self.mine.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(self.mine.read_at)

    def test_cannot_mark_someone_elses_notification_read(self):
        theirs = Notification.objects.exclude(pk=self.mine.pk).first()
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/notifications/{theirs.pk}/read/')

        self.assertEqual(resp.status_code, 404)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/notifications/').status_code, 401)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test notifications`
Expected: FAIL — `ModuleNotFoundError: No module named 'notifications'`.

- [ ] **Step 3: Create the app package and model**

`notifications/__init__.py` and `notifications/migrations/__init__.py` — empty files.

`notifications/apps.py`:

```python
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
```

`notifications/models.py`:

```python
from django.conf import settings
from django.db import models


class Notification(models.Model):
    """An event addressed to one user.

    This is the event feed, not the work queue. What is *waiting* for a role
    is derived from order status (see orders.views.InboxView) so it cannot
    drift; these rows drive the unread badge and the salesman's updates, and
    give later non-order events (bills, vouchers, stock) somewhere to live.
    """

    class Kind(models.TextChoices):
        ORDER_SUBMITTED = 'ORDER_SUBMITTED', 'Order submitted'
        ORDER_APPROVED = 'ORDER_APPROVED', 'Order approved'
        ORDER_REJECTED = 'ORDER_REJECTED', 'Order rejected'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=40, choices=Kind.choices)
    # Generic target so bills, vouchers and stock events slot in later
    # without a schema change.
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.kind} -> {self.recipient_id}"
```

`notifications/admin.py`:

```python
from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('kind', 'recipient', 'target_type', 'target_id', 'created_at', 'read_at')
    list_filter = ('kind',)
```

- [ ] **Step 4: Write the fan-out service**

`notifications/services.py`:

```python
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
```

- [ ] **Step 5: Write the serializer, viewset and urls**

`notifications/serializers.py`:

```python
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'kind', 'target_type', 'target_id', 'message', 'created_at', 'read_at']
        read_only_fields = fields
```

`notifications/views.py`:

```python
from django.utils import timezone
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only over the API - rows are created by workflow transitions."""

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Scoped to the requesting user, so a 404 (not a 403) is what someone
        # gets for another user's row - we do not confirm it exists.
        queryset = Notification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get('unread') == 'true':
            queryset = queryset.filter(read_at__isnull=True)
        return queryset

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])
        return Response(self.get_serializer(notification).data)
```

`notifications/urls.py`:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
```

- [ ] **Step 6: Register the app and its URLs**

In `mysite/settings.py`, add to `INSTALLED_APPS` after `'customers',`:

```python
    'notifications',
```

In `mysite/urls.py`, add after the `api/customers/` line:

```python
    path('api/notifications/', include('notifications.urls')),
```

- [ ] **Step 7: Migrate, test and commit**

```bash
python manage.py makemigrations notifications
python manage.py migrate
python manage.py test notifications
python manage.py test
```

Expected: 9 new tests PASS, whole suite OK.

```bash
cd c:/Medware
git add backend/Medware_Backend/notifications backend/Medware_Backend/mysite/settings.py backend/Medware_Backend/mysite/urls.py
git commit -m "feat: add notifications app with per-user event feed

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Approve and reject actions, and closing the side doors

**Files:**
- Modify: `orders/views.py`, `orders/serializers.py`
- Test: `orders/tests.py`

**Interfaces:**
- Consumes: `OrderRequest.Status` (Task 2); `notifications.services.notify`, `notifications.services.managers`, `Notification.Kind` (Task 3); `customers.Customer` (Task 1).
- Produces: `POST /api/orders/order-requests/<id>/approve/` and `POST /api/orders/order-requests/<id>/reject/`, both returning the serialized order. Nested item creation on `POST /api/orders/order-requests/`.

**Critical detail:** `RoleMethodPermission` keys off the HTTP **method**, and `allowed_roles_by_method['POST']` on this viewset is `['SALESMAN', 'MANAGER', 'CUSTOMER']`. A `POST` to `/approve/` therefore passes the class-level permission for a salesman. Each action must check the role itself. Without that, the endpoint built to stop a salesman approving their own order is the endpoint that lets them.

- [ ] **Step 1: Write the failing test**

Append to `orders/tests.py`:

```python
from audit.models import RequestTransition
from notifications.models import Notification
from orders.models import OrderReview


class OrderTransitionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='tr_slm', password='pass', role=User.Role.SALESMAN)
        self.manager = User.objects.create_user(username='tr_mgr', password='pass', role=User.Role.MANAGER)
        self.accountant = User.objects.create_user(username='tr_acc', password='pass', role=User.Role.ACCOUNTANT)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')

    def _order(self, status=OrderRequest.Status.PENDING):
        order = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman, status=status)
        OrderItem.objects.create(order_request=order, product=self.product,
                                 quantity=2, sell_price=Decimal('10.00'))
        return order

    def test_salesman_creates_an_order_with_nested_items(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'notes': 'urgent',
            'items': [
                {'product': self.product.pk, 'quantity': 3, 'sell_price': '10.00', 'note': 'cold chain'},
            ],
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        order = OrderRequest.objects.get(pk=resp.json()['id'])
        self.assertEqual(order.status, OrderRequest.Status.PENDING)
        self.assertEqual(order.salesman, self.salesman)      # server-derived
        self.assertEqual(order.origin, 'SALESMAN')           # server-derived
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().note, 'cold chain')
        self.assertEqual(order.total, Decimal('30.00'))

    def test_creating_an_order_notifies_every_manager(self):
        self.client.force_authenticate(user=self.salesman)

        self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        self.assertTrue(Notification.objects.filter(
            recipient=self.manager, kind=Notification.Kind.ORDER_SUBMITTED).exists())

    def test_manager_created_order_is_born_approved_with_a_review_row(self):
        """Decision (c): every order reaching the accountant has exactly one
        review, even when the manager is its author."""
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/order-requests/', {
            'customer': self.customer.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

        order = OrderRequest.objects.get(pk=resp.json()['id'])
        self.assertEqual(order.status, OrderRequest.Status.APPROVED)
        self.assertEqual(order.origin, 'MANAGER')
        self.assertEqual(order.reviews.count(), 1)
        self.assertEqual(order.reviews.first().manager, self.manager)

    def test_manager_approves_a_pending_order(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(order.status, OrderRequest.Status.APPROVED)
        self.assertEqual(order.reviews.filter(decision='APPROVE').count(), 1)
        self.assertTrue(RequestTransition.objects.filter(
            source_model='OrderRequest', source_id=str(order.pk),
            from_status='PENDING', to_status='APPROVED').exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.salesman, kind=Notification.Kind.ORDER_APPROVED).exists())

    def test_approval_freezes_the_balance_snapshots(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        order.refresh_from_db()
        self.assertEqual(order.previous_balance, Decimal('0.00'))
        self.assertEqual(order.new_balance, Decimal('20.00'))

    def test_salesman_cannot_approve(self):
        """RoleMethodPermission allows SALESMAN to POST on this viewset, so the
        action must check the role itself."""
        order = self._order()
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(order.status, OrderRequest.Status.PENDING)

    def test_accountant_cannot_approve(self):
        order = self._order()
        self.client.force_authenticate(user=self.accountant)

        self.assertEqual(
            self.client.post(f'/api/orders/order-requests/{order.pk}/approve/').status_code, 403)

    def test_approving_an_already_approved_order_is_a_conflict(self):
        order = self._order(status=OrderRequest.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/approve/')

        self.assertEqual(resp.status_code, 409)

    def test_rejecting_without_notes_is_refused(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/reject/',
                                {'notes': '   '}, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(order.status, OrderRequest.Status.PENDING)

    def test_rejecting_with_notes_records_and_notifies_the_reason(self):
        order = self._order()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/orders/order-requests/{order.pk}/reject/',
                                {'notes': 'Price above the agreed ceiling'}, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(order.status, OrderRequest.Status.REJECTED)
        review = order.reviews.get(decision='DECLINE')
        self.assertEqual(review.notes, 'Price above the agreed ceiling')
        notification = Notification.objects.get(
            recipient=self.salesman, kind=Notification.Kind.ORDER_REJECTED)
        self.assertIn('Price above the agreed ceiling', notification.message)


class OrderMutationLockTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='lk_slm', password='pass', role=User.Role.SALESMAN)
        self.manager = User.objects.create_user(username='lk_mgr', password='pass', role=User.Role.MANAGER)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')

    def _order(self, status):
        return OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman, status=status)

    def test_manager_can_change_quantities_while_pending(self):
        order = self._order(OrderRequest.Status.PENDING)
        item = OrderItem.objects.create(order_request=order, product=self.product,
                                        quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/orders/order-items/{item.pk}/', {'quantity': 5}, format='json')

        item.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(item.quantity, 5)

    def test_items_cannot_be_added_to_an_approved_order(self):
        """Otherwise a line lands underneath an approval, changing its value."""
        order = self._order(OrderRequest.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/order-items/', {
            'order_request': order.pk, 'product': self.product.pk,
            'quantity': 1, 'sell_price': '10.00',
        }, format='json')

        self.assertEqual(resp.status_code, 409)

    def test_items_cannot_be_edited_on_an_approved_order(self):
        order = self._order(OrderRequest.Status.APPROVED)
        item = OrderItem.objects.create(order_request=order, product=self.product,
                                        quantity=2, sell_price=Decimal('10.00'))
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/orders/order-items/{item.pk}/', {'quantity': 9}, format='json')

        item.refresh_from_db()
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(item.quantity, 2)

    def test_reviews_cannot_be_posted_directly(self):
        """A review posted by hand would walk around the state machine."""
        order = self._order(OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/orders/reviews/', {
            'order': order.pk, 'decision': 'APPROVE', 'notes': '',
        }, format='json')

        order.refresh_from_db()
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(order.status, OrderRequest.Status.PENDING)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test orders.tests.OrderTransitionTests orders.tests.OrderMutationLockTests`
Expected: FAIL — 404 on the `/approve/` URL, and the nested-items create returning an order with no items.

- [ ] **Step 3: Add nested item write to the serializer**

In `orders/serializers.py`, change `items` on `OrderRequestSerializer` from `read_only=True` to a writable nested field and add `create`:

```python
class OrderRequestSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    customer_name = serializers.CharField(source='customer.name', read_only=True, default=None)
    salesman_name = serializers.CharField(source='salesman.username', read_only=True, default=None)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderRequest
        fields = [
            'id', 'origin', 'customer', 'customer_name', 'salesman', 'salesman_name',
            'created_at', 'status', 'notes', 'previous_balance', 'new_balance',
            'total', 'items',
        ]
        read_only_fields = ['status', 'origin', 'salesman', 'previous_balance', 'new_balance']

    def create(self, validated_data):
        items = validated_data.pop('items', [])
        order = OrderRequest.objects.create(**validated_data)
        for item in items:
            OrderItem.objects.create(order_request=order, **item)
        return order
```

`OrderItemSerializer` must not require `order_request` when nested. Change it to:

```python
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order_request', 'product', 'quantity', 'sell_price', 'note', 'return_quantity']
        extra_kwargs = {'order_request': {'required': False}}
```

- [ ] **Step 4: Write the transition logic in the viewset**

In `orders/views.py`, add these imports at the top:

```python
from decimal import Decimal

from django.db import transaction
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from audit.models import RequestTransition
from notifications.models import Notification
from notifications.services import managers, notify
```

Add this helper above `OrderRequestViewSet`:

```python
def _record_transition(order, from_status, actor, notes=''):
    RequestTransition.objects.create(
        source_model='OrderRequest',
        source_id=str(order.pk),
        from_status=from_status,
        to_status=order.status,
        actor=actor,
        actor_role=getattr(actor, 'role', ''),
        notes=notes,
    )


def _approve(order, manager):
    """Flip to APPROVED, freezing the balances the customer agreed to.

    Reads finance.CustomerBalance but never writes it - moving the real
    balance is the accountant's finalize step, which is a later slice.
    """
    from finance.models import CustomerBalance

    from_status = order.status
    balance = CustomerBalance.objects.filter(customer=order.customer).first()
    order.previous_balance = balance.outstanding_balance if balance else Decimal('0')
    order.new_balance = order.previous_balance + order.total
    order.status = OrderRequest.Status.APPROVED
    order.save(update_fields=['status', 'previous_balance', 'new_balance'])

    OrderReview.objects.create(order=order, manager=manager, decision='APPROVE', notes='')
    _record_transition(order, from_status, manager)
    notify(
        [order.salesman] if order.salesman else [],
        Notification.Kind.ORDER_APPROVED,
        order,
        message=f'Order {order.pk} was approved.',
    )
```

Then add the actions and the create hook to `OrderRequestViewSet`:

```python
    def perform_create(self, serializer):
        """`origin` and `salesman` come from the requesting user, never the
        client. A manager's own order is approved in the same transaction, so
        every order reaching the accountant has exactly one review row."""
        user = self.request.user
        role = getattr(user, 'role', '')
        with transaction.atomic():
            order = serializer.save(
                origin=role if role in ('SALESMAN', 'MANAGER', 'CUSTOMER') else 'SALESMAN',
                salesman=user if role == 'SALESMAN' else None,
            )
            if role == 'MANAGER':
                _approve(order, user)
            else:
                notify(managers(), Notification.Kind.ORDER_SUBMITTED, order,
                       message=f'New order {order.pk} awaiting review.')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        # RoleMethodPermission checks the HTTP method, and POST is open to
        # SALESMAN on this viewset - so the role is checked here explicitly.
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may approve an order.')

        order = self.get_object()
        if order.status != OrderRequest.Status.PENDING:
            return Response(
                {'detail': f'An order in status {order.status} cannot be approved.'},
                status=http_status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            _approve(order, request.user)
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may reject an order.')

        notes = (request.data.get('notes') or '').strip()
        if not notes:
            raise ValidationError({'notes': 'A rejection reason is required.'})

        order = self.get_object()
        if order.status != OrderRequest.Status.PENDING:
            return Response(
                {'detail': f'An order in status {order.status} cannot be rejected.'},
                status=http_status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            from_status = order.status
            order.status = OrderRequest.Status.REJECTED
            order.save(update_fields=['status'])
            OrderReview.objects.create(order=order, manager=request.user,
                                       decision='DECLINE', notes=notes)
            _record_transition(order, from_status, request.user, notes=notes)
            notify(
                [order.salesman] if order.salesman else [],
                Notification.Kind.ORDER_REJECTED,
                order,
                message=f'Order {order.pk} was rejected: {notes}',
            )
        return Response(self.get_serializer(order).data)
```

- [ ] **Step 5: Close the side doors**

Still in `orders/views.py`, add this guard to `OrderItemViewSet`:

```python
    def _assert_parent_pending(self, order):
        if order.status != OrderRequest.Status.PENDING:
            raise Conflict(f'Order {order.pk} is {order.status} and its items are frozen.')

    def perform_create(self, serializer):
        self._assert_parent_pending(serializer.validated_data['order_request'])
        serializer.save()

    def perform_update(self, serializer):
        self._assert_parent_pending(serializer.instance.order_request)
        serializer.save()

    def perform_destroy(self, instance):
        self._assert_parent_pending(instance.order_request)
        instance.delete()
```

Define `Conflict` once, near the top of `orders/views.py` below the imports:

```python
class Conflict(APIException):
    """409 - the request is valid but the target is in the wrong state."""
    status_code = http_status.HTTP_409_CONFLICT
    default_detail = 'This record is in a state that does not allow the change.'
```

and add `APIException` to the `rest_framework.exceptions` import line.

Make reviews read-only by changing `OrderReviewViewSet` to a read-only viewset:

```python
class OrderReviewViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only: reviews are written by the approve/reject actions, never
    posted directly - a hand-written review walks around the state machine."""

    queryset = OrderReview.objects.all()
    serializer_class = OrderReviewSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT'],
    }
```

Add `mixins` to the `rest_framework` import at the top: `from rest_framework import mixins, permissions, viewsets`.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python manage.py test orders`
Expected: all PASS, including the 15 new tests.

- [ ] **Step 7: Run the whole suite and commit**

```bash
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/orders
git commit -m "feat: add order approve and reject actions with audit and notifications

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: The role-scoped Requests inbox

**Files:**
- Modify: `orders/views.py`, `orders/urls.py`
- Test: `orders/tests.py`

**Interfaces:**
- Consumes: `OrderRequest.Status` (Task 2), `Notification` (Task 3).
- Produces: `GET /api/orders/inbox/` returning `{"role": "<role>", "count": <int>, "items": [...]}` where each item is `{"kind": "ORDER_PENDING"|"ORDER_REJECTED", "order": <serialized order>, "message": "<string>", "notification_id": <int|null>}`.

- [ ] **Step 1: Write the failing test**

Append to `orders/tests.py`:

```python
class InboxTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='ib_slm', password='pass', role=User.Role.SALESMAN)
        self.other_salesman = User.objects.create_user(username='ib_slm2', password='pass', role=User.Role.SALESMAN)
        self.manager = User.objects.create_user(username='ib_mgr', password='pass', role=User.Role.MANAGER)
        self.accountant = User.objects.create_user(username='ib_acc', password='pass', role=User.Role.ACCOUNTANT)
        self.warehouse = User.objects.create_user(username='ib_wh', password='pass', role=User.Role.WAREHOUSE_WORKER)
        self.customer = Customer.objects.create(name='Al Noor Pharmacy')

        self.pending = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.PENDING)
        self.approved = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.APPROVED)

    def test_manager_inbox_holds_the_pending_orders(self):
        self.client.force_authenticate(user=self.manager)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['role'], 'MANAGER')
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['order']['id'], self.pending.pk)
        self.assertEqual(body['items'][0]['kind'], 'ORDER_PENDING')

    def test_accountant_inbox_holds_the_approved_orders(self):
        self.client.force_authenticate(user=self.accountant)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual([i['order']['id'] for i in body['items']], [self.approved.pk])

    def test_warehouse_inbox_is_empty_until_finance_lands(self):
        self.client.force_authenticate(user=self.warehouse)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['count'], 0)

    def test_salesman_inbox_holds_their_unread_rejections_only(self):
        rejected = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.REJECTED)
        mine = notify([self.salesman], Notification.Kind.ORDER_REJECTED, rejected,
                      message='Order rejected: too expensive')[0]
        notify([self.other_salesman], Notification.Kind.ORDER_REJECTED, rejected,
               message='Not yours')

        self.client.force_authenticate(user=self.salesman)
        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['notification_id'], mine.pk)
        self.assertEqual(body['items'][0]['order']['id'], rejected.pk)

    def test_a_read_rejection_leaves_the_salesman_inbox(self):
        rejected = OrderRequest.objects.create(
            origin='SALESMAN', customer=self.customer, salesman=self.salesman,
            status=OrderRequest.Status.REJECTED)
        row = notify([self.salesman], Notification.Kind.ORDER_REJECTED, rejected, message='x')[0]
        self.client.force_authenticate(user=self.salesman)

        self.client.post(f'/api/notifications/{row.pk}/read/')

        self.assertEqual(self.client.get('/api/orders/inbox/').json()['count'], 0)

    def test_customer_cannot_read_the_inbox(self):
        account = User.objects.create_user(username='ib_cust', password='pass', role=User.Role.CUSTOMER)
        self.client.force_authenticate(user=account)

        self.assertEqual(self.client.get('/api/orders/inbox/').status_code, 403)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/orders/inbox/').status_code, 401)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test orders.tests.InboxTests`
Expected: FAIL — 404, the URL does not exist.

- [ ] **Step 3: Write the inbox view**

Append to `orders/views.py`:

```python
class InboxView(APIView):
    """What is waiting for the requesting user.

    For the queue roles this derives from order status, so it cannot drift:
    an order is in the manager's queue because it *is* pending, not because a
    row somewhere says so. The salesman's rows are events rather than work,
    so they come from unread notifications.
    """

    permission_classes = [permissions.IsAuthenticated]

    QUEUE_STATUS_BY_ROLE = {
        'MANAGER': OrderRequest.Status.PENDING,
        'ACCOUNTANT': OrderRequest.Status.APPROVED,
        # Empty until the finance slice introduces FINALIZED orders.
        'WAREHOUSE_WORKER': OrderRequest.Status.FINALIZED,
    }

    def get(self, request):
        role = getattr(request.user, 'role', '')
        if role not in list(self.QUEUE_STATUS_BY_ROLE) + ['SALESMAN']:
            raise PermissionDenied('This role has no request inbox.')

        if role == 'SALESMAN':
            items = self._salesman_updates(request)
        else:
            items = self._queue(request, self.QUEUE_STATUS_BY_ROLE[role])

        return Response({'role': role, 'count': len(items), 'items': items})

    def _queue(self, request, status_value):
        orders = OrderRequest.objects.filter(status=status_value).order_by('created_at')
        return [
            {
                'kind': f'ORDER_{status_value}',
                'order': OrderRequestSerializer(order, context={'request': request}).data,
                'message': '',
                'notification_id': None,
            }
            for order in orders
        ]

    def _salesman_updates(self, request):
        unread = Notification.objects.filter(
            recipient=request.user,
            kind=Notification.Kind.ORDER_REJECTED,
            read_at__isnull=True,
        )
        items = []
        for notification in unread:
            order = OrderRequest.objects.filter(pk=notification.target_id).first()
            if order is None:
                continue
            items.append({
                'kind': 'ORDER_REJECTED',
                'order': OrderRequestSerializer(order, context={'request': request}).data,
                'message': notification.message,
                'notification_id': notification.pk,
            })
        return items
```

Add `APIView` to the imports at the top of `orders/views.py`:

```python
from rest_framework.views import APIView
```

- [ ] **Step 4: Register the URL**

In `orders/urls.py`, import the view and add the path **before** `path('', include(router.urls))` so the router's catch-all cannot shadow it:

```python
from .views import InboxView

urlpatterns = [
    path('inbox/', InboxView.as_view(), name='order-inbox'),
    path('', include(router.urls)),
]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python manage.py test orders.tests.InboxTests`
Expected: 7 tests PASS.

- [ ] **Step 6: Run the whole suite and commit**

```bash
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/orders
git commit -m "feat: add the role-scoped requests inbox endpoint

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Frontend types, services and permissions

**Files:**
- Create: `src/features/orders/types/orders.ts`, `src/features/orders/services/orders.service.ts`, `src/features/orders/index.ts`
- Modify: `src/features/auth/Permissions.tsx`, `src/i18n/ar.ts`

**Interfaces:**
- Consumes: the endpoints from Tasks 1–5.
- Produces: types `OrderRequest`, `OrderItem`, `OrderInboxItem`, `AppNotification`, `Customer`; service functions `getOrders`, `getOrderById`, `postOrder`, `approveOrder`, `rejectOrder`, `getInbox`, `getUnreadNotifications`, `markNotificationRead`, `getCustomers`; permission resource keys `orders` and `orderRequests`.

- [ ] **Step 1: Write the types**

Create `src/features/orders/types/orders.ts`:

```ts
// These mirror the DRF serializers in backend/Medware_Backend/orders. The API
// names foreign keys after the model field (`customer`, `product`), never with
// an `Id` suffix, and read-only labels arrive as `*_name`.

export type OrderStatus = "PENDING" | "APPROVED" | "REJECTED" | "FINALIZED"

export interface OrderItem {
    id: string
    order_request?: string | number
    product: string | number
    quantity: number
    sell_price: number
    note: string
    return_quantity: number
}

export interface OrderRequest {
    id: string
    origin: string
    customer: string | number
    customer_name?: string | null
    salesman: string | number | null
    salesman_name?: string | null
    created_at: string
    status: OrderStatus
    notes: string
    previous_balance: number | null
    new_balance: number | null
    total: number
    items: OrderItem[]
}

export interface OrderInboxItem {
    kind: string
    order: OrderRequest
    message: string
    notification_id: number | null
}

export interface OrderInbox {
    role: string
    count: number
    items: OrderInboxItem[]
}

export interface AppNotification {
    id: number
    kind: string
    target_type: string
    target_id: string
    message: string
    created_at: string
    read_at: string | null
}

export interface Customer {
    id: string
    name: string
    phone: string
    address: string
    notes: string
    user: string | number | null
    created_at: string
}
```

- [ ] **Step 2: Write the service**

Create `src/features/orders/services/orders.service.ts`:

```ts
import ax from "../../../services/api"
import type { AppNotification, Customer, OrderInbox, OrderRequest } from "../types/orders"

const ordersUrl = "/orders/order-requests/"

export const getOrders = async (status?: string): Promise<OrderRequest[]> => {
	const res = await ax.get<OrderRequest[]>(ordersUrl, {
		params: status ? { status } : undefined,
	})
	return res.data
}

export const getOrderById = async (id: string): Promise<OrderRequest> => {
	const res = await ax.get<OrderRequest>(`${ordersUrl}${id}/`)
	return res.data
}

// `status`, `origin` and `salesman` are set by the server and must not be sent.
export const postOrder = async (data: {
	customer: string | number
	notes: string
	items: Array<{ product: string | number; quantity: number; sell_price: number; note: string }>
}) => {
	const res = await ax.post<OrderRequest>(ordersUrl, data)
	return res.data
}

export const approveOrder = async (id: string): Promise<OrderRequest> => {
	const res = await ax.post<OrderRequest>(`${ordersUrl}${id}/approve/`)
	return res.data
}

// The backend returns 400 when `notes` is blank - a rejection never reaches a
// salesman without a reason.
export const rejectOrder = async (id: string, notes: string): Promise<OrderRequest> => {
	const res = await ax.post<OrderRequest>(`${ordersUrl}${id}/reject/`, { notes })
	return res.data
}

export const getInbox = async (): Promise<OrderInbox> => {
	const res = await ax.get<OrderInbox>("/orders/inbox/")
	return res.data
}

export const getUnreadNotifications = async (): Promise<AppNotification[]> => {
	const res = await ax.get<AppNotification[]>("/notifications/", { params: { unread: "true" } })
	return res.data
}

export const markNotificationRead = async (id: number) => {
	const res = await ax.post(`/notifications/${id}/read/`)
	return res.data
}

export const getCustomers = async (): Promise<Customer[]> => {
	const res = await ax.get<Customer[]>("/customers/")
	return res.data
}
```

Create `src/features/orders/index.ts`:

```ts
export { ordersRoutes } from "./orders.routes"
```

This import will fail until Task 7 creates `orders.routes.ts`. Create the file in Task 7, not here — do not add `index.ts` to any import yet.

- [ ] **Step 3: Add the permission entries**

In `src/features/auth/Permissions.tsx`, the `Permissions` type has an `orders` key declared `dataType: Suppliers` — a copy-paste slip. Fix it and add the new resource. Replace that entry:

```ts
    orders: {
        dataType: OrderRequest
        actions: Actions
    }
    orderApproval: {
        dataType: OrderRequest
        actions: Actions
    }
```

and add the import at the top of the file:

```ts
import type { OrderRequest } from "../orders/types/orders"
```

Then fill the per-role blocks. In `MANAGER`, replace its `orders: {` entry:

```ts
        orders: {
            read: true,
            create: true,
            update: true,
            delete: true
        },
        orderApproval: {
            read: true,
            create: true,
            update: true,
            delete: false
        },
```

In `SALESMAN`:

```ts
        orders: {
            read: true,
            create: true,
            update: true,
            delete: false
        },
        orderApproval: {
            read: false,
            create: false,
            update: false,
            delete: false
        },
```

In `ACCOUNTANT` and `WAREHOUSE_WORKER`:

```ts
        orders: {
            read: true,
            create: false,
            update: false,
            delete: false
        },
        orderApproval: {
            read: false,
            create: false,
            update: false,
            delete: false
        },
```

In `GUEST` and `CUSTOMER`:

```ts
        orders: {
            read: false,
            create: false,
            update: false,
            delete: false
        },
        orderApproval: {
            read: false,
            create: false,
            update: false,
            delete: false
        },
```

- [ ] **Step 4: Add the Arabic strings**

In `src/i18n/ar.ts`, add these keys immediately after the `details: "تفاصيل",` line:

```ts
    requests: "الطلبات الواردة",
    orders: "الطلبات",
    newOrder: "طلب جديد",
    customer: "العميل",
    salesman: "المندوب",
    orderTotal: "إجمالي الطلب",
    previousBalance: "الرصيد السابق",
    newBalance: "الرصيد الجديد",
    lineTotal: "إجمالي السطر",
    note: "ملاحظة",
    approve: "قبول",
    reject: "رفض",
    addItem: "إضافة صنف",
    removeItem: "حذف الصنف",
    OrderStatus: {
        PENDING: "بانتظار المراجعة",
        APPROVED: "مقبول",
        REJECTED: "مرفوض",
        FINALIZED: "مكتمل"
    },
    Orders_: {
        rejectTitle: "رفض الطلب",
        rejectReason: "سبب الرفض",
        rejectReasonRequired: "سبب الرفض مطلوب.",
        customerRequired: "العميل مطلوب.",
        itemsRequired: "يجب إضافة صنف واحد على الأقل.",
        quantityMin: "يجب أن تكون الكمية أكبر من صفر.",
        priceMin: "لا يمكن أن يكون السعر سالبًا.",
        serverError: "حدث خطأ أثناء معالجة الطلب.",
        createSuccess: "تم إنشاء الطلب",
        approveSuccess: "تم قبول الطلب",
        rejectSuccess: "تم رفض الطلب",
        emptyInbox: "لا يوجد ما ينتظر إجراءً"
    },
```

The existing top-level `Orders: "طلبات",` key stays — it labels the navigation dropdown. The new group is named `Orders_` to avoid colliding with it, since i18next cannot have a key be both a string and an object.

- [ ] **Step 5: Verify it compiles and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
```

Expected: exit 0. `index.ts` referencing a missing `orders.routes` is the one acceptable failure here — if it appears, delete `src/features/orders/index.ts` and recreate it in Task 7.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/orders frontend/src/features/auth/Permissions.tsx frontend/src/i18n/ar.ts
git commit -m "feat: add order types, services and permissions

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Orders list and detail pages

**Files:**
- Create: `src/features/orders/pages/OrdersPage.tsx`, `src/features/orders/pages/OrderDetailsPage.tsx`, `src/features/orders/orders.routes.ts`, `src/features/orders/index.ts`
- Modify: `src/router.tsx`

**Interfaces:**
- Consumes: everything from Task 6.
- Produces: `ordersRoutes` exported from `src/features/orders/index.ts`, registering `/app/orders` (`OrdersPage`) and `/app/orders/:orderId` (`OrderDetailsPage`).

**UI constraint:** `OrdersPage` mirrors the structure of `src/features/products/pages/SupplierBillsPage.tsx` — the same `TableSettings` / `TableFilter` / `DebouncedInput` toolbar above a `Table`, the same `Toast` for success, the same `hasPermission` gating on action buttons, the same `useOpenMenu` for modals. Read that file before writing this one and follow it.

- [ ] **Step 1: Write the list page**

Create `src/features/orders/pages/OrdersPage.tsx`:

```tsx
import { HugeiconsIcon } from "@hugeicons/react"
import { Plus, ViewIcon } from "@hugeicons/core-free-icons"
import { useQuery } from "@tanstack/react-query"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import DebouncedInput from "../../../components/DebouncedInput"
import { Table } from "../../../components/Table"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import Text from "../../../components/Text"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { getOrders } from "../services/orders.service"
import type { OrderRequest } from "../types/orders"

export const OrdersPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const navigate = useNavigate()
    const { t } = useTranslation()

    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState('')
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        id: true,
        customer: true,
        status: true,
    })

    const { data } = useQuery({ queryKey: ["orders"], queryFn: () => getOrders() })

    const columns: Array<ColumnDef<TableFeatures, OrderRequest>> = [
        {
            id: "actions",
            enableColumnFilter: false,
            enableCellSelection: false,
            enableSorting: false,
            enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    <Button
                        className="dark:text-accent-medium text-accent-dark dark:hover:text-accent-extraLight hover:text-accent-dark"
                        onClick={() => navigate(`/app/orders/${row.original.id}/`, {
                            state: { location: "orders", details: row.original.customer_name ?? "" },
                        })}
                        size="xs" variants="ghost"
                        leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />}>{t("details")}</Button>
                </div>
            )
        },
        {
            meta: { filterVariants: "value" },
            id: "customer",
            enableSorting: true,
            header: t("customer"),
            accessorFn: (row) => row.customer_name ?? String(row.customer ?? ""),
            cell: ({ row }) => row.original.customer_name ?? String(row.original.customer ?? ""),
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "value" },
            id: "salesman",
            enableSorting: true,
            header: t("salesman"),
            accessorFn: (row) => row.salesman_name ?? "",
            cell: ({ row }) => row.original.salesman_name ?? "",
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "value" },
            id: "status",
            enableSorting: true,
            header: t("status"),
            accessorFn: (row) => t(`OrderStatus.${row.status}`),
            cell: ({ row }) => t(`OrderStatus.${row.original.status}`),
            filterFn: filterFn_includesString
        },
        {
            meta: { filterVariants: "range" },
            id: "total",
            enableSorting: true,
            header: t("orderTotal"),
            accessorKey: "total",
            filterFn: filterFn_inNumberRange
        },
        {
            meta: { filterVariants: "range" },
            id: "id",
            enableGrouping: false,
            enableSorting: true,
            header: t("id"),
            accessorKey: "id",
            filterFn: filterFn_inNumberRange
        },
    ]

    return (
        <div>
            <div className="flex items-center gap-x-3 mb-8">
                {hasPermission(user, "orders", "create") &&
                    <Button onClick={() => navigate("/app/orders/new", { state: { location: "newOrder" } })}
                        variants="border" size="sm" iconOnly
                        leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                <TableSettings<OrderRequest>
                    columns={columns}
                    columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                    grouping={grouping} setGrouping={setGrouping} />
                <TableFilter<OrderRequest> columns={columns} columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                <DebouncedInput
                    fieldset={false}
                    rounded="full"
                    className="w-44"
                    placeholder={t("search") + "..."}
                    value={globalFilter}
                    onChange={setGlobalFilter}
                />
            </div>
            {data && data.length > 0 ? <Table<OrderRequest>
                columns={columns}
                data={data}
                tableKey="orders"
                columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                columnVisibility={columnVisibility}
                setColumnVisibility={setColumnVisibility}
                sorting={sorting}
                setSorting={setSorting}
                grouping={grouping}
                setGrouping={setGrouping}
                globalFilter={globalFilter}
                setGlobalFilter={setGlobalFilter}
            /> : <Text>{t("Orders_.emptyInbox")}</Text>}
        </div>
    )
}
```

- [ ] **Step 2: Write the detail page with approve and reject**

Create `src/features/orders/pages/OrderDetailsPage.tsx`:

```tsx
import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon } from "@hugeicons/core-free-icons"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useParams } from "react-router"
import Button from "../../../components/Button"
import ControlledTextArea from "../../../components/ControlledTextArea"
import Form from "../../../components/Form"
import Model from "../../../components/Model"
import { Table } from "../../../components/Table"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { approveOrder, getOrderById, rejectOrder } from "../services/orders.service"
import type { ColumnDef, SortingState, TableFeatures } from "@tanstack/react-table"
import type { OrderItem } from "../types/orders"

type RejectFields = { notes: string }

export const OrderDetailsPage = () => {
    const { orderId } = useParams<{ orderId: string }>()
    const user = useBoundStore(state => state.authSlice.user)
    const { t } = useTranslation()
    const queryClient = useQueryClient()
    const [sorting, setSorting] = useState<SortingState>([])
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const { isOpen: isOpenReject, setIsOpen: setIsOpenReject, ref: rejectRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const orderKey = ["orders", orderId] as const
    const { data: order } = useQuery({
        queryKey: orderKey,
        queryFn: () => getOrderById(String(orderId)),
        enabled: Boolean(orderId),
    })

    const { control, handleSubmit, reset, setError, formState: { errors } } = useForm<RejectFields>({
        defaultValues: { notes: "" },
        mode: "all",
    })

    const approve = useMutation({
        mutationFn: () => approveOrder(String(orderId)),
        onSuccess() {
            setSuccessMessage(t("Orders_.approveSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["orders"] })
        },
    })

    const rejectMutation = useMutation({
        mutationFn: (notes: string) => rejectOrder(String(orderId), notes),
        onSuccess() {
            setIsOpenReject(false)
            reset({ notes: "" })
            setSuccessMessage(t("Orders_.rejectSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["orders"] })
        },
        onError() {
            setError("root.server", { type: "server", message: t("Orders_.serverError") })
        },
    })

    const columns: Array<ColumnDef<TableFeatures, OrderItem>> = [
        { id: "product", header: t("item"), accessorKey: "product", enableSorting: true },
        { id: "quantity", header: t("quantity"), accessorKey: "quantity", enableSorting: true },
        { id: "sell_price", header: t("unit_price"), accessorKey: "sell_price", enableSorting: true },
        {
            id: "line_total",
            header: t("lineTotal"),
            accessorFn: (row) => Number(row.quantity) * Number(row.sell_price),
            cell: ({ row }) => Number(row.original.quantity) * Number(row.original.sell_price),
            enableSorting: true,
        },
        { id: "note", header: t("note"), accessorKey: "note", enableSorting: false },
    ]

    if (!order) return <Text>{t("Orders_.emptyInbox")}</Text>

    const canDecide = hasPermission(user, "orderApproval", "update") && order.status === "PENDING"

    return (
        <div>
            <Model title={t("Orders_.rejectTitle")} isOpen={isOpenReject} onClick={() => setIsOpenReject(false)} ref={rejectRef}>
                <Form
                    ServerError={errors.root?.server}
                    onSubmit={handleSubmit((values) => rejectMutation.mutate(values.notes))}
                    Buttons={<Button type="submit">{t("reject")}</Button>}>
                    <ControlledTextArea<RejectFields>
                        rules={{
                            shouldUnregister: true,
                            required: { message: t("Orders_.rejectReasonRequired"), value: true },
                        }}
                        placeholder={t("Orders_.rejectReason")}
                        name="notes"
                        control={control}
                    />
                </Form>
            </Model>

            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div className="grid grid-cols-2 gap-x-6 mb-6">
                <Text>{t("customer")}: {order.customer_name}</Text>
                <Text>{t("salesman")}: {order.salesman_name ?? ""}</Text>
                <Text>{t("status")}: {t(`OrderStatus.${order.status}`)}</Text>
                <Text>{t("date")}: {order.created_at?.slice(0, 10)}</Text>
            </div>

            <Table<OrderItem> tableKey="orderItems" columns={columns} data={order.items}
                sorting={sorting} setSorting={setSorting} />

            <div className="mt-6 grid grid-cols-3 gap-x-6">
                <Text>{t("orderTotal")}: {order.total}</Text>
                <Text>{t("previousBalance")}: {order.previous_balance ?? "-"}</Text>
                <Text>{t("newBalance")}: {order.new_balance ?? "-"}</Text>
            </div>

            {canDecide && <div className="mt-6 flex gap-x-3">
                <Button onClick={() => approve.mutate()}>{t("approve")}</Button>
                <Button variants="ghost"
                    className="dark:text-error text-error"
                    onClick={() => setIsOpenReject(true)}>{t("reject")}</Button>
            </div>}
        </div>
    )
}
```

- [ ] **Step 3: Register the routes**

Create `src/features/orders/orders.routes.ts`:

```ts
import type { RouteObject } from "react-router";
import { OrdersPage } from "./pages/OrdersPage";
import { OrderDetailsPage } from "./pages/OrderDetailsPage";

export const ordersRoutes: RouteObject[] = [
    {
        path: "orders",
        Component: OrdersPage,
    },
    {
        path: "orders/:orderId",
        Component: OrderDetailsPage,
    },
]
```

Create (or recreate) `src/features/orders/index.ts`:

```ts
export { ordersRoutes } from "./orders.routes"
```

In `src/router.tsx`, add the import and spread it into the `/app` children alongside the others:

```ts
import { ordersRoutes } from "./features/orders";
```

```ts
                children:[
                    ...inventoryRoutes,
                    ...peoductsRoutes,
                    ...ordersRoutes
                ]
```

- [ ] **Step 4: Add the `status` string**

`t("status")` is used above. In `src/i18n/ar.ts`, add after the `requests:` key added in Task 6:

```ts
    status: "الحالة",
```

- [ ] **Step 5: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
npm run build
```

Expected: both clean.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/orders frontend/src/router.tsx frontend/src/i18n/ar.ts
git commit -m "feat: add orders list and detail pages with approve and reject

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: The create-order page with its line-items editor

**Files:**
- Create: `src/features/orders/pages/OrderCreatePage.tsx`
- Modify: `src/features/orders/orders.routes.ts`

**Interfaces:**
- Consumes: `postOrder`, `getCustomers` (Task 6); `getProducts` from `src/features/products/services/products.service`.
- Produces: route `/app/orders/new`.

**This is the one genuinely new component in the app.** Every existing form edits a single flat entity; nothing has repeating rows. It uses `useFieldArray` from react-hook-form. Totals render live for feedback only — the saved order always shows the server's numbers, because a JS float and a Postgres `DECIMAL` can round differently.

- [ ] **Step 1: Write the page**

Create `src/features/orders/pages/OrderCreatePage.tsx`:

```tsx
import { HugeiconsIcon } from "@hugeicons/react"
import { Plus, Trash } from "@hugeicons/core-free-icons"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useFieldArray, useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import ControlledTextArea from "../../../components/ControlledTextArea"
import Form from "../../../components/Form"
import { ControlledSearchSelectInput } from "../../../components/SearchSelectInput"
import Text from "../../../components/Text"
import { getProducts } from "../../products/services/products.service"
import { getCustomers, postOrder } from "../services/orders.service"

type OrderFormFields = {
    customer: string
    notes: string
    items: Array<{ product: string; quantity: string; sell_price: string; note: string }>
}

const emptyItem = { product: "", quantity: "1", sell_price: "0", note: "" }

export const OrderCreatePage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()

    const { data: customers = [] } = useQuery({ queryKey: ["customers"], queryFn: getCustomers })
    // getProducts is typed as returning a single Products by mistake in the
    // products service; the endpoint returns a list, so normalise here.
    const { data: products } = useQuery({ queryKey: ["productsList"], queryFn: getProducts })
    const productList = Array.isArray(products) ? products : []

    const customerOptions = customers.map((c) => ({ value: String(c.id), label: c.name }))
    const productOptions = productList.map((p) => ({ value: String(p.id), label: p.name }))

    const { control, handleSubmit, watch, setValue, setError, formState: { errors } } =
        useForm<OrderFormFields>({
            defaultValues: { customer: "", notes: "", items: [emptyItem] },
            mode: "all",
        })

    const { fields, append, remove } = useFieldArray({ control, name: "items" })
    const watchedItems = watch("items")

    // Live feedback only. The server recomputes and its response is the truth.
    const previewTotal = watchedItems.reduce(
        (sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.sell_price) || 0), 0)

    const create = useMutation({
        mutationFn: postOrder,
        onSuccess(order) {
            navigate(`/app/orders/${order.id}/`, { state: { location: "orders" } })
        },
        onError() {
            setError("root.server", { type: "server", message: t("Orders_.serverError") })
        },
    })

    const onSubmit = (values: OrderFormFields) => {
        const items = values.items.filter((item) => item.product)
        if (items.length === 0) {
            setError("root.server", { type: "server", message: t("Orders_.itemsRequired") })
            return
        }
        create.mutate({
            customer: Number(values.customer),
            notes: values.notes,
            items: items.map((item) => ({
                product: Number(item.product),
                quantity: Number(item.quantity),
                sell_price: Number(item.sell_price),
                note: item.note,
            })),
        })
    }

    return (
        <Form
            ServerError={errors.root?.server}
            onSubmit={handleSubmit(onSubmit)}
            Buttons={<Button type="submit">{t("newOrder")}</Button>}>

            <div className="grid grid-cols-2 gap-x-6">
                <ControlledSearchSelectInput<OrderFormFields>
                    control={control}
                    name="customer"
                    label={t("customer")}
                    rules={{ required: { message: t("Orders_.customerRequired"), value: true } }}
                    options={customerOptions}
                    placeholder={t("search") + "..."}
                />
            </div>

            <div className="mt-6 space-y-3">
                {fields.map((field, index) => (
                    <div key={field.id} className="grid grid-cols-5 gap-x-3 items-start">
                        <ControlledSearchSelectInput<OrderFormFields>
                            control={control}
                            name={`items.${index}.product`}
                            label={t("item")}
                            options={productOptions}
                            placeholder={t("search") + "..."}
                        />
                        <ControlledInput<OrderFormFields>
                            name={`items.${index}.quantity`}
                            type="number"
                            control={control}
                            rules={{ min: { message: t("Orders_.quantityMin"), value: 1 } }}
                        />
                        <ControlledInput<OrderFormFields>
                            name={`items.${index}.sell_price`}
                            type="number"
                            control={control}
                            rules={{ min: { message: t("Orders_.priceMin"), value: 0 } }}
                        />
                        <ControlledInput<OrderFormFields>
                            name={`items.${index}.note`}
                            control={control}
                        />
                        <Button
                            type="button"
                            className="dark:text-error text-error"
                            size="xs" variants="ghost" iconOnly
                            onClick={() => remove(index)}
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />
                    </div>
                ))}
            </div>

            <div className="mt-3">
                <Button type="button" variants="border" size="sm"
                    onClick={() => append({ ...emptyItem })}
                    leftIcon={<HugeiconsIcon size={16} icon={Plus} />}>{t("addItem")}</Button>
            </div>

            <ControlledTextArea<OrderFormFields>
                placeholder={t("notes")}
                name="notes"
                control={control}
            />

            <Text className="mt-4">{t("orderTotal")}: {previewTotal}</Text>
        </Form>
    )
}
```

Selecting a product prefills its price: add this effect import and block after `watchedItems` is declared.

```tsx
    // Adding a product prefills the line's price from the catalogue; it stays
    // editable, and the value is frozen on the order once saved.
    useEffect(() => {
        watchedItems.forEach((item, index) => {
            if (!item.product) return
            const product = productList.find((p) => String(p.id) === String(item.product))
            if (product && (item.sell_price === "0" || item.sell_price === "")) {
                setValue(`items.${index}.sell_price`, String(product.retail_price ?? 0))
            }
        })
    }, [watchedItems, productList, setValue])
```

Add `useEffect` to the React import at the top:

```tsx
import { useEffect } from "react"
```

- [ ] **Step 2: Register the route**

In `src/features/orders/orders.routes.ts`, import the page and add the route **before** `orders/:orderId` so the static segment is unambiguous:

```ts
import { OrderCreatePage } from "./pages/OrderCreatePage";
```

```ts
    {
        path: "orders/new",
        Component: OrderCreatePage,
    },
```

- [ ] **Step 3: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
npm run build
```

Expected: both clean. If `getProducts` produces a type error, that is the mistyped service noted in the code comment — normalise with `Array.isArray` as shown rather than changing the shared service in this task.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/orders
git commit -m "feat: add the create-order page with a line-items editor

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: The Requests tab, navigation, and the Products landing page

**Files:**
- Create: `src/features/orders/pages/RequestsPage.tsx`
- Modify: `src/features/orders/orders.routes.ts`, `src/components/Navigation.tsx`, `src/features/auth/pages/LoginPage.tsx`, `src/features/auth/pages/registerWizard/Step2.tsx`

**Interfaces:**
- Consumes: `getInbox`, `markNotificationRead` (Task 6); the routes from Tasks 7–8.
- Produces: route `/app/requests`.

- [ ] **Step 1: Write the Requests page**

Create `src/features/orders/pages/RequestsPage.tsx`:

```tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import { useNavigate } from "react-router"
import Button from "../../../components/Button"
import Text from "../../../components/Text"
import { getInbox, markNotificationRead } from "../services/orders.service"

export const RequestsPage = () => {
    const { t } = useTranslation()
    const navigate = useNavigate()
    const queryClient = useQueryClient()

    // Polled rather than pushed: the project has no websockets, and adding
    // Channels would be an infrastructure change of its own.
    const { data } = useQuery({
        queryKey: ["ordersInbox"],
        queryFn: getInbox,
        refetchInterval: 30000,
    })

    const dismiss = useMutation({
        mutationFn: markNotificationRead,
        onSuccess() {
            queryClient.invalidateQueries({ queryKey: ["ordersInbox"] })
        },
    })

    if (!data || data.count === 0) return <Text>{t("Orders_.emptyInbox")}</Text>

    return (
        <div className="space-y-3">
            {data.items.map((item) => (
                <div key={`${item.kind}-${item.order.id}-${item.notification_id ?? "q"}`}
                    className="flex items-center justify-between gap-x-4 p-4 rounded-xl border border-light-border-secondary dark:border-dark-border-tertiary">
                    <div>
                        <Text>{item.order.customer_name} — {t("orderTotal")}: {item.order.total}</Text>
                        {item.message && <Text>{item.message}</Text>}
                    </div>
                    <div className="flex gap-x-2">
                        <Button size="xs" variants="ghost"
                            onClick={() => navigate(`/app/orders/${item.order.id}/`, {
                                state: { location: "orders", details: item.order.customer_name ?? "" },
                            })}>{t("details")}</Button>
                        {item.notification_id !== null &&
                            <Button size="xs" variants="ghost"
                                onClick={() => dismiss.mutate(item.notification_id as number)}>
                                {t("Suppliers.confirm")}
                            </Button>}
                    </div>
                </div>
            ))}
        </div>
    )
}
```

- [ ] **Step 2: Register the route**

In `src/features/orders/orders.routes.ts`, import and add:

```ts
import { RequestsPage } from "./pages/RequestsPage";
```

```ts
    {
        path: "requests",
        Component: RequestsPage,
    },
```

- [ ] **Step 3: Make the Orders dropdown real and add Requests**

In `src/components/Navigation.tsx`, the `Orders` dropdown currently holds two copy-pasted inventory links (`categories` and `items` pointing at `/app/inventory/...`). Replace **both of those `<Button>` elements inside the `isOpenOrders` dropdown** with:

```tsx
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname === "/app/orders"}
              leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
              onClick={() => { navigarte("/app/orders", { state: { location: "orders" } }); }}
            >
              {t('orders')}
            </Button>
            <Button
              size='sm'
              className={`w-full justify-start`}
              variants='ghost'
              active={location.pathname.includes("/app/requests")}
              leftIcon={<HugeiconsIcon size={22} icon={RightToLeftListDashIcon} />}
              onClick={() => { navigarte("/app/requests", { state: { location: "requests" } }); }}
            >
              {t('requests')}
            </Button>
```

`active` on the orders entry is an exact match so it does not stay lit while the user is on `/app/orders/new` or a detail page.

- [ ] **Step 4: Pin Products first and make it the landing page**

Still in `Navigation.tsx`, move the existing Products `<Button>` (the one calling `navigarte("/app/products", …)`) so it is the **first** entry after the user dropdown `</div>`, before the Suppliers dropdown.

Then in `src/features/auth/pages/LoginPage.tsx`:

```tsx
navigate("/app/products", { state: { location: "Products" } })
```

and identically in `src/features/auth/pages/registerWizard/Step2.tsx`:

```tsx
navigate("/app/products", { state: { location: "Products" } })
```

Both currently point at `/app/supplier/bills`.

- [ ] **Step 5: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
grep -rn "app/supplier/bills" src/features/auth/
npx tsc -b
npm run build
```

Expected: the grep prints nothing (both redirects moved), and both builds are clean.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/orders frontend/src/components/Navigation.tsx frontend/src/features/auth
git commit -m "feat: add the requests tab and land every role on products

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Manual verification

There is no browser automation in this environment, so these are for you to walk:

- [ ] Sign in as a manager — you land on Products, and it is the first nav entry.
- [ ] As a salesman, create an order with two lines; it saves and opens showing status "بانتظار المراجعة" and the server's total.
- [ ] As a manager, the Requests tab lists that order; opening it shows the lines.
- [ ] Change a quantity on the pending order as the manager, then approve — status becomes "مقبول", and previous/new balance are filled.
- [ ] As the salesman, the Requests tab shows nothing for an approved order but shows a rejection with its reason after a manager rejects one.
- [ ] Rejecting with an empty reason is refused by the form.
- [ ] As an accountant, the Requests tab lists approved orders. As a warehouse worker it is empty (correct until the finance slice).

## Self-review

**Spec coverage.** `customers` app → Task 1. Notification table → Task 3. State machine, read-only status, approve/reject, 400 on blank notes, 409 on wrong state, audit rows, balance snapshots, manager auto-approve with a review row → Tasks 2 and 4. Closed side doors (reviews read-only, items frozen off `PENDING`) → Task 4. Inbox → Task 5. Frontend routes, pages, line-items editor, Requests tab, Products landing, `Permissions.tsx` fix → Tasks 6–9. Django admin registration for `Customer` → Task 1 Step 5. Every spec requirement has a task.

**Placeholder scan.** No TBDs. Every code step carries literal code. The one deliberately deferred item — the accountant's finalize action — is named as out of scope in the spec and produces an intentionally empty accountant/warehouse inbox, which Task 5 tests explicitly rather than leaving unstated.

**Type consistency.** `OrderRequest.Status` members are used identically in Tasks 2, 4 and 5. `notify(recipients, kind, target, message='')` and `managers()` are defined in Task 3 and called with that exact signature in Task 4. The frontend `OrderRequest`/`OrderItem`/`OrderInbox` types defined in Task 6 are the ones consumed in Tasks 7–9. Service names (`getOrders`, `getOrderById`, `postOrder`, `approveOrder`, `rejectOrder`, `getInbox`, `getUnreadNotifications`, `markNotificationRead`, `getCustomers`) are defined once in Task 6 and used unchanged thereafter. The i18n group is `Orders_` everywhere, chosen because the existing top-level `Orders` key is a string and i18next cannot have a key be both.

**Known risk — measured, not assumed.** Exactly one existing test builds an `OrderRequest` with a `User` as its customer: `users/tests_security.py:109`. Step 7c repairs it and strengthens it. `scripts/method_matrix.py` does too but is never run by Django's test discovery; Step 7d keeps it working anyway. Step 7b covers the `scope_to_user` change these depend on.

**Deliberate inconsistency, carried forward.** `ReturnRequest.customer` stays a foreign key to `User` while `OrderRequest.customer` becomes a `Customer`. Repointing returns is not in this slice — returns have no UI, no workflow and no tests exercising them yet, and dragging them in widens a slice that is already nine tasks. The consequence is that `scope_to_user` is called with different `customer_field` arguments depending on the viewset, which Step 7b comments at both call sites. **When the returns slice is built, `ReturnRequest.customer` should move to `Customer` and those call sites should converge.**
