# Customer Approval, Role Badge and Navigation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a salesman or manager create a customer — a salesman's becoming an approval request the manager acts on — so orders can finally be raised through the app, and restructure the navigation so everything built so far is reachable.

**Architecture:** The customer approval workflow deliberately mirrors the order one already in the codebase: a `TextChoices` status that is read-only over the serializer and moves only through `approve`/`reject` action endpoints, each writing an `audit.RequestTransition` row and a `Notification` in one transaction. It reuses the existing generic inbox rather than adding a second queue. The navigation drops its collapsible dropdowns for the static section headings in the user's reference screenshot.

**Tech Stack:** Django 6.0.5, DRF 3.17.1, PostgreSQL. Frontend: React 19, React Router 8, TanStack Query 5, TanStack Table 9, react-hook-form 7, i18next (Arabic only), TypeScript 6, Vite 8.

**Spec:** `docs/superpowers/specs/2026-09-05-customers-finance-and-navigation-design.md` — this plan covers Parts A, B and C only. Parts D (finance panel) and E (products/inventory) get their own plan.

## Global Constraints

- Backend lives at `c:/Medware/backend/Medware_Backend`; run `python manage.py …` from there, in the **foreground** (the suite takes over two minutes — pass `timeout: 400000`).
- Backend commits go in the outer repo `c:/Medware` on branch `back`. Frontend commits go in the **separate nested repo** `c:/Medware/frontemd` on branch `frontend`.
- The backend suite is the gate for every backend task: `python manage.py test` must stay green (**107** tests pass before this plan starts).
- **There is no frontend test runner and none is to be added.** The frontend gate is `npx tsc -b` exiting 0 and `npm run build` succeeding.
- `status`, `created_by` and `rejection_notes` are **read-only in the serializer**. `status` moves only through the action endpoints.
- Every state transition writes an `audit.RequestTransition` row.
- Rejecting with blank `notes` returns **400**. A transition from a state that does not allow it returns **409**.
- Both actions check `request.user.role == 'MANAGER'` **inside the action body** — `RoleMethodPermission` keys off the HTTP method, so a `POST` to `/approve/` passes the class-level check for a salesman.
- **Do not change Suppliers or Purchases.** The user's explicit instruction: those two navigation entries keep their existing targets and labels. They are only repositioned under a heading.
- Every user-facing frontend string goes through `t(...)` with the key added to `src/i18n/ar.ts`. A missing key renders the raw English identifier.
- Reuse the existing components — `Button`, `Model`, `Form`, `Table`, `TableFilter`, `TableSettings`, `DebouncedInput`, `Toast`, `Text`, `ControlledInput`, `ControlledTextArea`, `Dropdown`, `useOpenMenu`, `hasPermission`. No new UI or form library.
- Frontend types mirror the serializers exactly: foreign keys named after the model field, read-only labels as `*_name`.
- The registration approval gate is deliberately disabled in this build (`validate_role` and the `is_verified` hooks are commented in `users/serializers.py`). **Do not touch it.**

---

### Task 1: Customer status, creation side effects and scoping

**Files:**
- Modify: `customers/models.py`, `customers/serializers.py`, `customers/views.py`, `customers/admin.py`, `notifications/models.py`
- Test: `customers/tests.py`

**Interfaces:**
- Consumes: `notifications.services.notify(recipients, kind, target, message='')` and `managers()`; `audit.models.RequestTransition`.
- Produces: `Customer.Status` with members `PENDING`, `APPROVED`, `REJECTED` (values equal names); `Customer.created_by`, `Customer.rejection_notes`; `Notification.Kind.CUSTOMER_SUBMITTED` / `CUSTOMER_APPROVED` / `CUSTOMER_REJECTED`; `customers.views._record_customer_transition(customer, from_status, actor, notes='')`; `GET /api/customers/?status=`.

- [ ] **Step 1: Write the failing test**

Replace the whole of `customers/tests.py` with:

```python
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework.test import APIClient

from audit.models import RequestTransition
from customers.models import Customer
from notifications.models import Notification
from orders.models import OrderRequest
from users.models import User


class CustomerModelTests(TestCase):
    def test_an_internal_customer_has_no_user_account(self):
        """Outside the website a customer is data, not a login."""
        customer = Customer.objects.create(name='Al Noor Pharmacy', phone='0100000000')

        self.assertIsNone(customer.user)

    def test_a_customer_can_be_linked_to_a_website_account_later(self):
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

    def test_a_new_customer_starts_pending(self):
        self.assertEqual(Customer.objects.create(name='Dar Al Shifa').status,
                         Customer.Status.PENDING)


class CustomerCreationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='cc_mgr', password='pass', role=User.Role.MANAGER)
        self.other_manager = User.objects.create_user(username='cc_mgr2', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='cc_slm', password='pass', role=User.Role.SALESMAN)
        self.warehouse = User.objects.create_user(username='cc_wh', password='pass', role=User.Role.WAREHOUSE_WORKER)

    def test_a_salesman_creates_a_customer_as_a_pending_request(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 201)
        customer = Customer.objects.get(pk=resp.json()['id'])
        self.assertEqual(customer.status, Customer.Status.PENDING)
        self.assertEqual(customer.created_by, self.salesman)

    def test_a_salesman_creating_a_customer_notifies_every_manager(self):
        self.client.force_authenticate(user=self.salesman)

        self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        for manager in (self.manager, self.other_manager):
            self.assertTrue(Notification.objects.filter(
                recipient=manager, kind=Notification.Kind.CUSTOMER_SUBMITTED).exists())

    def test_a_manager_creates_a_customer_already_approved(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        customer = Customer.objects.get(pk=resp.json()['id'])
        self.assertEqual(customer.status, Customer.Status.APPROVED)
        self.assertEqual(customer.created_by, self.manager)

    def test_a_manager_created_customer_does_not_notify_anyone(self):
        """Nothing is waiting on it, so nobody needs telling."""
        self.client.force_authenticate(user=self.manager)

        self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(Notification.objects.count(), 0)

    def test_creation_writes_an_audit_row(self):
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertTrue(RequestTransition.objects.filter(
            source_model='Customer', source_id=str(resp.json()['id']),
            to_status='PENDING').exists())

    def test_a_warehouse_worker_cannot_create_a_customer(self):
        self.client.force_authenticate(user=self.warehouse)

        resp = self.client.post('/api/customers/', {'name': 'Dar Al Shifa'}, format='json')

        self.assertEqual(resp.status_code, 403)

    def test_status_cannot_be_set_from_the_request_body(self):
        """The regression guard: status moves only through the actions."""
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post('/api/customers/',
                                {'name': 'Dar Al Shifa', 'status': 'APPROVED'}, format='json')

        self.assertEqual(Customer.objects.get(pk=resp.json()['id']).status,
                         Customer.Status.PENDING)


class CustomerScopingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='cs_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='cs_slm', password='pass', role=User.Role.SALESMAN)
        self.other_salesman = User.objects.create_user(username='cs_slm2', password='pass', role=User.Role.SALESMAN)

        self.approved = Customer.objects.create(name='Approved Co', status=Customer.Status.APPROVED)
        self.mine = Customer.objects.create(name='My Pending', status=Customer.Status.PENDING,
                                            created_by=self.salesman)
        self.theirs = Customer.objects.create(name='Their Pending', status=Customer.Status.PENDING,
                                              created_by=self.other_salesman)

    def test_a_manager_sees_every_customer(self):
        self.client.force_authenticate(user=self.manager)

        names = {row['name'] for row in self.client.get('/api/customers/').json()}

        self.assertEqual(names, {'Approved Co', 'My Pending', 'Their Pending'})

    def test_a_salesman_sees_approved_customers_and_only_their_own_pending(self):
        self.client.force_authenticate(user=self.salesman)

        names = {row['name'] for row in self.client.get('/api/customers/').json()}

        self.assertEqual(names, {'Approved Co', 'My Pending'})

    def test_the_status_filter_narrows_the_list(self):
        self.client.force_authenticate(user=self.manager)

        rows = self.client.get('/api/customers/?status=PENDING').json()

        self.assertEqual({row['name'] for row in rows}, {'My Pending', 'Their Pending'})

    def test_an_unknown_status_is_rejected(self):
        self.client.force_authenticate(user=self.manager)

        self.assertEqual(self.client.get('/api/customers/?status=NOPE').status_code, 400)

    def test_the_list_carries_the_creator_name(self):
        self.client.force_authenticate(user=self.manager)

        rows = self.client.get('/api/customers/?status=PENDING').json()

        self.assertEqual({row['created_by_name'] for row in rows}, {'cs_slm', 'cs_slm2'})

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/customers/').status_code, 401)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test customers`
Expected: FAIL — `AttributeError: type object 'Customer' has no attribute 'Status'`.

- [ ] **Step 3: Add the status, creator and rejection fields**

In `customers/models.py`, add the `Status` class and three fields to `Customer`, directly above `name`:

```python
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending manager approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected by manager'

    # A salesman's customer arrives as a request; a manager's is born approved.
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers_created',
    )
    rejection_notes = models.TextField(blank=True)
```

- [ ] **Step 4: Add the notification kinds**

In `notifications/models.py`, add three members to `Notification.Kind`, after `ORDER_REJECTED`:

```python
        CUSTOMER_SUBMITTED = 'CUSTOMER_SUBMITTED', 'Customer submitted'
        CUSTOMER_APPROVED = 'CUSTOMER_APPROVED', 'Customer approved'
        CUSTOMER_REJECTED = 'CUSTOMER_REJECTED', 'Customer rejected'
```

- [ ] **Step 5: Expose the new fields read-only on the serializer**

Replace `customers/serializers.py` with:

```python
from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'address', 'notes', 'user', 'created_at',
            'status', 'created_by', 'created_by_name', 'rejection_notes',
        ]
        # `status` moves only through the approve/reject actions; leaving it
        # writable would let a salesman approve their own customer with a POST.
        read_only_fields = ['created_at', 'status', 'created_by', 'rejection_notes']
```

- [ ] **Step 6: Open creation to salesmen, scope the list, and record the transition**

Replace `customers/views.py` with:

```python
from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError

from audit.models import RequestTransition
from mysite.filters import filter_by_query_params
from notifications.models import Notification
from notifications.services import managers, notify
from users.permissions import RoleMethodPermission

from .models import Customer
from .serializers import CustomerSerializer

# Roles that see every customer regardless of who created it.
CUSTOMER_WIDE_ROLES = ('MANAGER', 'ACCOUNTANT')


def _record_customer_transition(customer, from_status, actor, notes=''):
    RequestTransition.objects.create(
        source_model='Customer',
        source_id=str(customer.pk),
        from_status=from_status,
        to_status=customer.status,
        actor=actor,
        actor_role=getattr(actor, 'role', ''),
        notes=notes,
    )


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, RoleMethodPermission]
    allowed_roles_by_method = {
        'GET': ['MANAGER', 'ACCOUNTANT', 'SALESMAN'],
        # A salesman meets the customer; one who cannot add a customer cannot
        # raise an order. Theirs arrives as a request for a manager to approve.
        'POST': ['SALESMAN', 'MANAGER'],
        'PUT': ['SALESMAN', 'MANAGER'],
        'PATCH': ['SALESMAN', 'MANAGER'],
        'DELETE': ['MANAGER'],
    }

    def get_queryset(self):
        # Scope first, then filter: a query parameter must never widen what a
        # user can see.
        queryset = super().get_queryset().select_related('created_by')
        user = self.request.user
        if not (user.is_superuser or getattr(user, 'role', '') in CUSTOMER_WIDE_ROLES):
            # A salesman sees approved customers plus their own unapproved
            # ones - never another salesman's pending record.
            queryset = queryset.filter(
                Q(status=Customer.Status.APPROVED) | Q(created_by=user))

        queryset = filter_by_query_params(queryset, self.request, {'id': 'id'})

        status_value = self.request.query_params.get('status')
        if status_value:
            if status_value not in Customer.Status.values:
                raise ValidationError({'status': f"'{status_value}' is not a valid status."})
            queryset = queryset.filter(status=status_value)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        is_manager = getattr(user, 'role', '') == 'MANAGER'
        with transaction.atomic():
            customer = serializer.save(
                created_by=user,
                status=Customer.Status.APPROVED if is_manager else Customer.Status.PENDING,
            )
            _record_customer_transition(customer, '', user)
            if not is_manager:
                notify(managers(), Notification.Kind.CUSTOMER_SUBMITTED, customer,
                       message=f'New customer {customer.name} awaiting approval.')
```

- [ ] **Step 7: Show the new fields in the admin**

In `customers/admin.py`, replace the `list_display` and `search_fields` lines:

```python
    list_display = ('name', 'phone', 'status', 'created_by', 'user')
    list_filter = ('status',)
    search_fields = ('name', 'phone')
```

- [ ] **Step 8: Migrate and run the tests**

```bash
python manage.py makemigrations customers notifications
python manage.py migrate
python manage.py test customers
```

Expected: the new migrations apply, and `customers` tests all pass.

- [ ] **Step 9: Run the whole suite and commit**

```bash
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/customers backend/Medware_Backend/notifications
git commit -m "feat: customers created by a salesman become approval requests

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Customer approve and reject actions

**Files:**
- Modify: `customers/views.py`
- Test: `customers/tests.py`

**Interfaces:**
- Consumes: `Customer.Status`, `_record_customer_transition`, `Notification.Kind` (Task 1).
- Produces: `POST /api/customers/<id>/approve/` and `POST /api/customers/<id>/reject/`, both returning the serialized customer.

- [ ] **Step 1: Write the failing test**

Append to `customers/tests.py`:

```python
class CustomerTransitionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='ct_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='ct_slm', password='pass', role=User.Role.SALESMAN)
        self.accountant = User.objects.create_user(username='ct_acc', password='pass', role=User.Role.ACCOUNTANT)

    def _pending(self):
        return Customer.objects.create(name='Dar Al Shifa', status=Customer.Status.PENDING,
                                       created_by=self.salesman)

    def test_a_manager_approves_a_pending_customer(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/approve/')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(customer.status, Customer.Status.APPROVED)
        self.assertTrue(RequestTransition.objects.filter(
            source_model='Customer', source_id=str(customer.pk),
            from_status='PENDING', to_status='APPROVED').exists())
        self.assertTrue(Notification.objects.filter(
            recipient=self.salesman, kind=Notification.Kind.CUSTOMER_APPROVED).exists())

    def test_a_salesman_cannot_approve(self):
        """RoleMethodPermission allows SALESMAN to POST here, so the action
        must check the role itself."""
        customer = self._pending()
        self.client.force_authenticate(user=self.salesman)

        resp = self.client.post(f'/api/customers/{customer.pk}/approve/')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(customer.status, Customer.Status.PENDING)

    def test_an_accountant_cannot_approve(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.accountant)

        self.assertEqual(
            self.client.post(f'/api/customers/{customer.pk}/approve/').status_code, 403)

    def test_approving_an_already_approved_customer_is_a_conflict(self):
        customer = Customer.objects.create(name='Done', status=Customer.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        self.assertEqual(
            self.client.post(f'/api/customers/{customer.pk}/approve/').status_code, 409)

    def test_rejecting_without_notes_is_refused(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/reject/',
                                {'notes': '   '}, format='json')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(customer.status, Customer.Status.PENDING)

    def test_rejecting_records_and_notifies_the_reason(self):
        customer = self._pending()
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/reject/',
                                {'notes': 'Duplicate of an existing account'}, format='json')

        customer.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(customer.status, Customer.Status.REJECTED)
        self.assertEqual(customer.rejection_notes, 'Duplicate of an existing account')
        notification = Notification.objects.get(
            recipient=self.salesman, kind=Notification.Kind.CUSTOMER_REJECTED)
        self.assertIn('Duplicate of an existing account', notification.message)

    def test_a_customer_created_without_a_creator_still_rejects_cleanly(self):
        """`created_by` is SET_NULL, so the notify list can be empty."""
        customer = Customer.objects.create(name='Orphan', status=Customer.Status.PENDING)
        self.client.force_authenticate(user=self.manager)

        resp = self.client.post(f'/api/customers/{customer.pk}/reject/',
                                {'notes': 'No owner'}, format='json')

        self.assertEqual(resp.status_code, 200)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test customers.tests.CustomerTransitionTests`
Expected: FAIL — 404, the `/approve/` URL does not exist.

- [ ] **Step 3: Add the actions**

In `customers/views.py`, extend the imports at the top:

```python
from rest_framework import permissions, status as http_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
```

Then add both actions to `CustomerViewSet`:

```python
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        # RoleMethodPermission checks the HTTP method, and POST is open to
        # SALESMAN on this viewset - so the role is checked here explicitly.
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may approve a customer.')

        with transaction.atomic():
            customer = Customer.objects.select_for_update().get(pk=self.get_object().pk)
            if customer.status != Customer.Status.PENDING:
                return Response(
                    {'detail': f'A customer in status {customer.status} cannot be approved.'},
                    status=http_status.HTTP_409_CONFLICT,
                )
            from_status = customer.status
            customer.status = Customer.Status.APPROVED
            customer.save(update_fields=['status'])
            _record_customer_transition(customer, from_status, request.user)
            notify(
                [customer.created_by] if customer.created_by else [],
                Notification.Kind.CUSTOMER_APPROVED,
                customer,
                message=f'Customer {customer.name} was approved.',
            )
        return Response(self.get_serializer(customer).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if getattr(request.user, 'role', '') != 'MANAGER':
            raise PermissionDenied('Only a manager may reject a customer.')

        notes = (request.data.get('notes') or '').strip()
        if not notes:
            raise ValidationError({'notes': 'A rejection reason is required.'})

        with transaction.atomic():
            customer = Customer.objects.select_for_update().get(pk=self.get_object().pk)
            if customer.status != Customer.Status.PENDING:
                return Response(
                    {'detail': f'A customer in status {customer.status} cannot be rejected.'},
                    status=http_status.HTTP_409_CONFLICT,
                )
            from_status = customer.status
            customer.status = Customer.Status.REJECTED
            customer.rejection_notes = notes
            customer.save(update_fields=['status', 'rejection_notes'])
            _record_customer_transition(customer, from_status, request.user, notes=notes)
            notify(
                [customer.created_by] if customer.created_by else [],
                Notification.Kind.CUSTOMER_REJECTED,
                customer,
                message=f'Customer {customer.name} was rejected: {notes}',
            )
        return Response(self.get_serializer(customer).data)
```

- [ ] **Step 4: Run the tests and the whole suite, then commit**

```bash
python manage.py test customers
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/customers
git commit -m "feat: add customer approve and reject actions

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Orders require an approved customer, and the inbox carries customer rows

**Files:**
- Modify: `orders/serializers.py`, `orders/views.py`
- Test: `orders/tests.py`

**Interfaces:**
- Consumes: `Customer.Status`, `Notification.Kind.CUSTOMER_REJECTED` (Tasks 1–2).
- Produces: inbox rows gain a `customer` key alongside `order`; one of the two is always `null`.

- [ ] **Step 1: Write the failing test**

Append to `orders/tests.py`:

```python
from customers.models import Customer as CustomerModel


class OrderRequiresApprovedCustomerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.salesman = User.objects.create_user(username='ac_slm', password='pass', role=User.Role.SALESMAN)
        self.product = Product.objects.create(name='Paracetamol', retail_price='10.00')
        self.client.force_authenticate(user=self.salesman)

    def _post(self, customer):
        return self.client.post('/api/orders/order-requests/', {
            'customer': customer.pk,
            'items': [{'product': self.product.pk, 'quantity': 1, 'sell_price': '10.00'}],
        }, format='json')

    def test_an_order_for_an_approved_customer_is_accepted(self):
        customer = CustomerModel.objects.create(name='Approved Co',
                                                status=CustomerModel.Status.APPROVED)

        self.assertEqual(self._post(customer).status_code, 201)

    def test_an_order_for_a_pending_customer_is_refused(self):
        """An order approved against a customer the company has not accepted
        is a record nobody can act on."""
        customer = CustomerModel.objects.create(name='Pending Co',
                                                status=CustomerModel.Status.PENDING,
                                                created_by=self.salesman)

        resp = self._post(customer)

        self.assertEqual(resp.status_code, 400)
        self.assertIn('customer', resp.json())

    def test_an_order_for_a_rejected_customer_is_refused(self):
        customer = CustomerModel.objects.create(name='Rejected Co',
                                                status=CustomerModel.Status.REJECTED,
                                                created_by=self.salesman)

        self.assertEqual(self._post(customer).status_code, 400)


class InboxCustomerRowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username='ic_mgr', password='pass', role=User.Role.MANAGER)
        self.salesman = User.objects.create_user(username='ic_slm', password='pass', role=User.Role.SALESMAN)

    def test_the_manager_inbox_carries_pending_customers(self):
        pending = CustomerModel.objects.create(name='Pending Co',
                                               status=CustomerModel.Status.PENDING,
                                               created_by=self.salesman)
        CustomerModel.objects.create(name='Approved Co', status=CustomerModel.Status.APPROVED)
        self.client.force_authenticate(user=self.manager)

        body = self.client.get('/api/orders/inbox/').json()

        customer_rows = [i for i in body['items'] if i['kind'] == 'CUSTOMER_PENDING']
        self.assertEqual(len(customer_rows), 1)
        self.assertEqual(customer_rows[0]['customer']['id'], pending.pk)
        self.assertIsNone(customer_rows[0]['order'])

    def test_the_salesman_inbox_carries_their_unread_customer_rejections(self):
        rejected = CustomerModel.objects.create(name='Rejected Co',
                                                status=CustomerModel.Status.REJECTED,
                                                created_by=self.salesman)
        row = notify([self.salesman], Notification.Kind.CUSTOMER_REJECTED, rejected,
                     message='Customer Rejected Co was rejected: duplicate')[0]
        self.client.force_authenticate(user=self.salesman)

        body = self.client.get('/api/orders/inbox/').json()

        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['kind'], 'CUSTOMER_REJECTED')
        self.assertEqual(body['items'][0]['notification_id'], row.pk)
        self.assertEqual(body['items'][0]['customer']['id'], rejected.pk)

    def test_order_rows_still_carry_a_null_customer_key(self):
        customer = CustomerModel.objects.create(name='Approved Co',
                                                status=CustomerModel.Status.APPROVED)
        OrderRequest.objects.create(origin='SALESMAN', customer=customer,
                                    salesman=self.salesman,
                                    status=OrderRequest.Status.PENDING)
        self.client.force_authenticate(user=self.manager)

        body = self.client.get('/api/orders/inbox/').json()

        order_rows = [i for i in body['items'] if i['kind'] == 'ORDER_PENDING']
        self.assertEqual(len(order_rows), 1)
        self.assertIsNone(order_rows[0]['customer'])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test orders.tests.OrderRequiresApprovedCustomerTests orders.tests.InboxCustomerRowTests`
Expected: FAIL — the pending-customer order returns 201, and the inbox rows have no `customer` key.

- [ ] **Step 3: Refuse an order for a customer who is not approved**

In `orders/serializers.py`, add this method to `OrderRequestSerializer`, directly above `create`:

```python
    def validate_customer(self, value):
        # An order approved against a customer the company has not accepted is
        # a record nobody can act on. The manager sees the customer request in
        # the same inbox, so the wait is short.
        from customers.models import Customer

        if value.status != Customer.Status.APPROVED:
            raise serializers.ValidationError(
                f'This customer is {value.status} and cannot have orders raised for them yet.')
        return value
```

- [ ] **Step 4: Give every inbox row both keys, and add the customer rows**

In `orders/views.py`, add these imports:

```python
from customers.models import Customer
from customers.serializers import CustomerSerializer
```

In `InboxView`, replace `_queue` and `_salesman_updates` and add the two customer helpers:

```python
    def _queue(self, request, status_value):
        orders = (OrderRequest.objects
                  .filter(status=status_value)
                  .select_related('customer', 'salesman')
                  .prefetch_related('items')
                  .order_by('created_at'))
        return [
            {
                'kind': f'ORDER_{status_value}',
                'order': OrderRequestSerializer(order, context={'request': request}).data,
                'customer': None,
                'message': '',
                'notification_id': None,
            }
            for order in orders
        ]

    def _pending_customers(self, request):
        """Customer requests waiting on a manager - the same queue treatment as
        pending orders, derived from status so it cannot drift."""
        customers = (Customer.objects
                     .filter(status=Customer.Status.PENDING)
                     .select_related('created_by')
                     .order_by('created_at'))
        return [
            {
                'kind': 'CUSTOMER_PENDING',
                'order': None,
                'customer': CustomerSerializer(customer, context={'request': request}).data,
                'message': '',
                'notification_id': None,
            }
            for customer in customers
        ]

    def _salesman_updates(self, request):
        unread = list(Notification.objects.filter(
            recipient=request.user,
            kind__in=[Notification.Kind.ORDER_REJECTED, Notification.Kind.CUSTOMER_REJECTED],
            read_at__isnull=True,
        ))

        order_ids, customer_ids = [], []
        for notification in unread:
            try:
                target_pk = int(notification.target_id)
            except (TypeError, ValueError):
                continue
            if notification.kind == Notification.Kind.ORDER_REJECTED:
                order_ids.append(target_pk)
            else:
                customer_ids.append(target_pk)

        orders = {o.pk: o for o in OrderRequest.objects.filter(pk__in=order_ids)
                  .select_related('customer', 'salesman').prefetch_related('items')}
        customers = {c.pk: c for c in Customer.objects.filter(pk__in=customer_ids)
                     .select_related('created_by')}

        items = []
        for notification in unread:
            try:
                target_pk = int(notification.target_id)
            except (TypeError, ValueError):
                continue

            if notification.kind == Notification.Kind.ORDER_REJECTED:
                order = orders.get(target_pk)
                if order is None:
                    continue
                items.append({
                    'kind': 'ORDER_REJECTED',
                    'order': OrderRequestSerializer(order, context={'request': request}).data,
                    'customer': None,
                    'message': notification.message,
                    'notification_id': notification.pk,
                })
            else:
                customer = customers.get(target_pk)
                if customer is None:
                    continue
                items.append({
                    'kind': 'CUSTOMER_REJECTED',
                    'order': None,
                    'customer': CustomerSerializer(customer, context={'request': request}).data,
                    'message': notification.message,
                    'notification_id': notification.pk,
                })
        return items
```

Then in `InboxView.get`, give the manager both queues. Replace the branch that builds `items`:

```python
        if role == 'SALESMAN':
            items = self._salesman_updates(request)
        else:
            items = self._queue(request, self.QUEUE_STATUS_BY_ROLE[role])
            if role == 'MANAGER':
                items += self._pending_customers(request)
```

- [ ] **Step 5: Run the tests and the whole suite, then commit**

```bash
python manage.py test orders customers
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/orders
git commit -m "feat: orders need an approved customer, and the inbox carries customer requests

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Frontend customer types, service and permissions

**Files:**
- Create: `src/features/customers/types/customers.ts`, `src/features/customers/services/customers.service.ts`
- Modify: `src/features/auth/Permissions.tsx`, `src/i18n/ar.ts`

**Interfaces:**
- Consumes: the endpoints from Tasks 1–3.
- Produces: type `Customer`; services `getCustomers(status?)`, `postCustomer`, `putCustomer`, `deleteCustomer`, `approveCustomer`, `rejectCustomer`; permission key `customers` and `customerApproval`.

- [ ] **Step 1: Write the type**

Create `src/features/customers/types/customers.ts`:

```ts
// Mirrors customers.serializers.CustomerSerializer. `status`, `created_by` and
// `rejection_notes` are read-only server-side and must never be submitted.

export type CustomerStatus = "PENDING" | "APPROVED" | "REJECTED"

export interface Customer {
    id: string
    name: string
    phone: string
    address: string
    notes: string
    user: string | number | null
    created_at: string
    status: CustomerStatus
    created_by: string | number | null
    created_by_name?: string | null
    rejection_notes: string
}
```

- [ ] **Step 2: Write the service**

Create `src/features/customers/services/customers.service.ts`:

```ts
import ax from "../../../services/api"
import type { Customer } from "../types/customers"

const customersUrl = "/customers/"

export const getCustomers = async (status?: string): Promise<Customer[]> => {
	const res = await ax.get<Customer[]>(customersUrl, {
		params: status ? { status } : undefined,
	})
	return res.data
}

// `status`, `created_by` and `rejection_notes` are set by the server.
export const postCustomer = async (data: Pick<Customer, "name" | "phone" | "address" | "notes">) => {
	const res = await ax.post<Customer>(customersUrl, data)
	return res.data
}

export const putCustomer = async (id: string, data: Pick<Customer, "name" | "phone" | "address" | "notes">) => {
	const res = await ax.put<Customer>(`${customersUrl}${id}/`, data)
	return res.data
}

export const deleteCustomer = async (id: string) => {
	const res = await ax.delete(`${customersUrl}${id}/`)
	return res
}

export const approveCustomer = async (id: string): Promise<Customer> => {
	const res = await ax.post<Customer>(`${customersUrl}${id}/approve/`)
	return res.data
}

// The backend returns 400 when `notes` is blank - a rejection never reaches
// the salesman without a reason.
export const rejectCustomer = async (id: string, notes: string): Promise<Customer> => {
	const res = await ax.post<Customer>(`${customersUrl}${id}/reject/`, { notes })
	return res.data
}
```

- [ ] **Step 3: Add the permission entries**

In `src/features/auth/Permissions.tsx`, add to the `Permissions` type, after the `orderApproval` entry:

```ts
    customers: {
        dataType: Customer
        actions: Actions
    }
    customerApproval: {
        dataType: Customer
        actions: Actions
    }
```

and the import at the top:

```ts
import type { Customer } from "../customers/types/customers"
```

Then add both keys to **every** role block. `MANAGER`:

```ts
        customers: { read: true, create: true, update: true, delete: true },
        customerApproval: { read: true, create: true, update: true, delete: false },
```

`SALESMAN`:

```ts
        customers: { read: true, create: true, update: true, delete: false },
        customerApproval: { read: false, create: false, update: false, delete: false },
```

`ACCOUNTANT`:

```ts
        customers: { read: true, create: false, update: false, delete: false },
        customerApproval: { read: false, create: false, update: false, delete: false },
```

`WAREHOUSE_WORKER`, `GUEST` and `CUSTOMER`:

```ts
        customers: { read: false, create: false, update: false, delete: false },
        customerApproval: { read: false, create: false, update: false, delete: false },
```

- [ ] **Step 4: Add the Arabic strings**

In `src/i18n/ar.ts`, add after the `status: "الحالة",` key:

```ts
    customers: "العملاء",
    phone_: "الهاتف",
    address: "العنوان",
    createdBy: "أنشأه",
    home: "الرئيسية",
    employees: "الموظفون",
    settings: "الإعدادات",
    preferences: "التفضيلات",
    inbound: "الوارد",
    outbound: "الصادر",
    comingSoon: "قريبًا",
    ACCOUNTANT: "محاسب",
    SALESMAN: "مندوب مبيعات",
    WAREHOUSE_WORKER: "عامل مستودع",
    CUSTOMER: "عميل",
    MANAGER: "مدير",
    GUEST: "زائر",
    CustomerStatus: {
        PENDING: "بانتظار الموافقة",
        APPROVED: "معتمد",
        REJECTED: "مرفوض"
    },
    Customers_: {
        newCustomer: "إضافة عميل جديد",
        addCustomer: "أضف العميل",
        editCustomer: "تعديل العميل",
        deleteTitle: "حذف عميل",
        deleteConfirm: "هل أنت متأكد أنك تريد حذف هذا العميل؟",
        rejectTitle: "رفض العميل",
        rejectReason: "سبب الرفض",
        rejectReasonRequired: "سبب الرفض مطلوب.",
        nameRequired: "اسم العميل مطلوب.",
        serverError: "حدث خطأ أثناء معالجة العميل.",
        createSuccess: "تم إنشاء العميل",
        updateSuccess: "تم تحديث العميل بنجاح",
        deleteSuccess: "تم حذف العميل بنجاح",
        approveSuccess: "تمت الموافقة على العميل",
        rejectSuccess: "تم رفض العميل",
        pendingHint: "بانتظار موافقة المدير"
    },
```

`phone_` is named with a trailing underscore because a top-level `phone` key already exists and is in use.

- [ ] **Step 5: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
```

Expected: exit 0.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/customers frontend/src/features/auth/Permissions.tsx frontend/src/i18n/ar.ts
git commit -m "feat: add customer types, services and permissions

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: The Customers page

**Files:**
- Create: `src/features/customers/pages/CustomersPage.tsx`, `src/features/customers/customers.routes.ts`, `src/features/customers/index.ts`
- Modify: `src/router.tsx`

**Interfaces:**
- Consumes: everything from Task 4.
- Produces: `customersRoutes` exported from `src/features/customers/index.ts`, registering `/app/customers`.

**UI constraint:** mirror `src/features/products/pages/SupplierPage.tsx` — the same toolbar, `Table`, `Model` create/edit and delete modals, `Toast`, `useOpenMenu` and `hasPermission` gating. **Read that file before writing this one.**

- [ ] **Step 1: Write the page**

Create `src/features/customers/pages/CustomersPage.tsx`:

```tsx
import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon, Edit, Plus, Trash, ViewIcon } from "@hugeicons/core-free-icons"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { filterFn_includesString, filterFn_inNumberRange, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import ControlledInput from "../../../components/ControlledInput"
import ControlledTextArea from "../../../components/ControlledTextArea"
import DebouncedInput from "../../../components/DebouncedInput"
import Form from "../../../components/Form"
import Model from "../../../components/Model"
import { Table } from "../../../components/Table"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { approveCustomer, deleteCustomer, getCustomers, postCustomer, putCustomer, rejectCustomer } from "../services/customers.service"
import type { Customer } from "../types/customers"

type CustomerFields = { name: string; phone: string; address: string; notes: string }
type RejectFields = { notes: string }

const emptyCustomer: CustomerFields = { name: "", phone: "", address: "", notes: "" }

export const CustomersPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const { t } = useTranslation()
    const queryClient = useQueryClient()

    const { isOpen: isOpenAddModel, setIsOpen: setIsOpenAddModel, ref: addRef } = useOpenMenu()
    const { isOpen: isOpenDeleteModel, setIsOpen: setIsOpenDeleteModel, ref: deleteRef } = useOpenMenu()
    const { isOpen: isOpenRejectModel, setIsOpen: setIsOpenRejectModel, ref: rejectRef } = useOpenMenu()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState('')
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        id: true, name: true, status: true,
    })
    const [editingId, setEditingId] = useState<string | null>(null)
    const [deleteTarget, setDeleteTarget] = useState<Customer | null>(null)
    const [rejectTarget, setRejectTarget] = useState<Customer | null>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)

    const { data } = useQuery({ queryKey: ["customers"], queryFn: () => getCustomers() })

    const { control, handleSubmit, reset, setError, clearErrors, formState: { errors } } =
        useForm<CustomerFields>({ defaultValues: emptyCustomer, mode: "all" })

    const rejectForm = useForm<RejectFields>({ defaultValues: { notes: "" }, mode: "all" })

    const invalidate = () => queryClient.invalidateQueries({ queryKey: ["customers"] })

    const create = useMutation({ mutationFn: postCustomer })
    const update = useMutation({
        mutationFn: ({ id, values }: { id: string; values: CustomerFields }) => putCustomer(id, values),
    })
    const remove = useMutation({ mutationFn: (id: string) => deleteCustomer(id) })
    const approve = useMutation({
        mutationFn: (id: string) => approveCustomer(id),
        onSuccess() {
            setSuccessMessage(t("Customers_.approveSuccess")); setIsOpenToast(true); invalidate()
        },
        onError() { setError("root.server", { type: "server", message: t("Customers_.serverError") }) },
    })
    const rejectMutation = useMutation({
        mutationFn: ({ id, notes }: { id: string; notes: string }) => rejectCustomer(id, notes),
        onSuccess() {
            setIsOpenRejectModel(false); setRejectTarget(null); rejectForm.reset({ notes: "" })
            setSuccessMessage(t("Customers_.rejectSuccess")); setIsOpenToast(true); invalidate()
        },
        onError() {
            rejectForm.setError("root.server", { type: "server", message: t("Customers_.serverError") })
        },
    })

    useEffect(() => {
        if (!isOpenAddModel) { reset(emptyCustomer); clearErrors(); setEditingId(null) }
    }, [isOpenAddModel, clearErrors, reset])

    useEffect(() => {
        if (!isOpenToast) return
        const id = window.setTimeout(() => { setIsOpenToast(false); setSuccessMessage(null) }, 3000)
        return () => window.clearTimeout(id)
    }, [isOpenToast, setIsOpenToast])

    const onSubmit = (values: CustomerFields) => {
        clearErrors("root.server")
        const onError = () => setError("root.server", { type: "server", message: t("Customers_.serverError") })
        const onDone = (message: string) => {
            setIsOpenAddModel(false); setSuccessMessage(message); setIsOpenToast(true); invalidate()
        }
        if (editingId) {
            update.mutate({ id: editingId, values }, {
                onError, onSuccess: () => onDone(t("Customers_.updateSuccess")),
            })
            return
        }
        create.mutate(values, { onError, onSuccess: () => onDone(t("Customers_.createSuccess")) })
    }

    const columns: Array<ColumnDef<TableFeatures, Customer>> = [
        {
            id: "actions",
            enableColumnFilter: false, enableCellSelection: false,
            enableSorting: false, enableGrouping: false,
            header: t("actions"),
            cell: ({ row }) => (
                <div className="flex justify-center gap-x-2">
                    {hasPermission(user, "customerApproval", "update") && row.original.status === "PENDING" && <>
                        <Button
                            className="dark:text-accent-medium text-accent-dark"
                            size="xs" variants="ghost"
                            onClick={() => approve.mutate(row.original.id)}
                            leftIcon={<HugeiconsIcon size={18} icon={ViewIcon} />}>{t("approve")}</Button>
                        <Button
                            className="dark:text-error text-error"
                            size="xs" variants="ghost"
                            onClick={() => { setRejectTarget(row.original); setIsOpenRejectModel(true) }}>
                            {t("reject")}
                        </Button>
                    </>}
                    {hasPermission(user, "customers", "delete") &&
                        <Button
                            className="dark:text-error text-error dark:hover:text-dark-text-error-hover hover:text-light-text-error-hover"
                            onClick={() => { setDeleteTarget(row.original); setIsOpenDeleteModel(true) }}
                            size="xs" variants="ghost" iconOnly
                            leftIcon={<HugeiconsIcon size={18} icon={Trash} />} />}
                    {hasPermission(user, "customers", "update") &&
                        <Button
                            className="dark:text-accent-light text-accent-extraDark dark:hover:text-accent-extraLight hover:text-accent-dark"
                            onClick={() => {
                                setEditingId(row.original.id)
                                reset({
                                    name: row.original.name, phone: row.original.phone,
                                    address: row.original.address, notes: row.original.notes,
                                })
                                setIsOpenAddModel(true)
                            }}
                            size="xs" variants="ghost" iconOnly
                            leftIcon={<HugeiconsIcon size={18} icon={Edit} />} />}
                </div>
            ),
        },
        {
            meta: { filterVariants: "value" }, id: "name", enableSorting: true,
            header: t("name"), accessorKey: "name", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "phone", enableSorting: true,
            header: t("phone_"), accessorKey: "phone", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "status", enableSorting: true,
            header: t("status"),
            accessorFn: (row) => t(`CustomerStatus.${row.status}`),
            cell: ({ row }) => t(`CustomerStatus.${row.original.status}`),
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "created_by", enableSorting: true,
            header: t("createdBy"),
            accessorFn: (row) => row.created_by_name ?? "",
            cell: ({ row }) => row.original.created_by_name ?? "",
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "range" }, id: "id", enableGrouping: false,
            enableSorting: true, header: t("id"), accessorKey: "id",
            filterFn: filterFn_inNumberRange,
        },
    ]

    return (
        <div>
            <Model title={editingId ? t("Customers_.editCustomer") : t("Customers_.newCustomer")}
                isOpen={isOpenAddModel} onClick={() => setIsOpenAddModel(false)} ref={addRef}>
                <Form ServerError={errors.root?.server} onSubmit={handleSubmit(onSubmit)}
                    Buttons={<Button type="submit">{t("Customers_.addCustomer")}</Button>}>
                    <div className="grid grid-cols-2 gap-x-6">
                        <ControlledInput<CustomerFields>
                            name="name" control={control}
                            rules={{ shouldUnregister: true, required: { message: t("Customers_.nameRequired"), value: true } }} />
                        <ControlledInput<CustomerFields> name="phone" control={control}
                            rules={{ shouldUnregister: true }} />
                    </div>
                    <ControlledTextArea<CustomerFields> name="address" control={control}
                        placeholder={t("address")} rules={{ shouldUnregister: true }} />
                    <ControlledTextArea<CustomerFields> name="notes" control={control}
                        placeholder={t("notes")} rules={{ shouldUnregister: true }} />
                    {!hasPermission(user, "customerApproval", "update") &&
                        <Text className="mt-2">{t("Customers_.pendingHint")}</Text>}
                </Form>
            </Model>

            <Model title={t("Customers_.rejectTitle")} isOpen={isOpenRejectModel}
                onClick={() => setIsOpenRejectModel(false)} ref={rejectRef}>
                <Form ServerError={rejectForm.formState.errors.root?.server}
                    onSubmit={rejectForm.handleSubmit((values) => {
                        if (!rejectTarget) return
                        rejectMutation.mutate({ id: rejectTarget.id, notes: values.notes })
                    })}
                    Buttons={<Button type="submit">{t("reject")}</Button>}>
                    <ControlledTextArea<RejectFields> name="notes" control={rejectForm.control}
                        placeholder={t("Customers_.rejectReason")}
                        rules={{ shouldUnregister: true, required: { message: t("Customers_.rejectReasonRequired"), value: true } }} />
                </Form>
            </Model>

            <Model title={t("Customers_.deleteTitle")} isOpen={isOpenDeleteModel}
                onClick={() => setIsOpenDeleteModel(false)} ref={deleteRef}>
                <div className="p-4">
                    <Text>{t("Customers_.deleteConfirm")}</Text>
                    <div className="flex justify-end gap-x-2 mt-4">
                        <Button variants="ghost" onClick={() => { setIsOpenDeleteModel(false); setDeleteTarget(null) }}>
                            {t("Suppliers.cancel")}
                        </Button>
                        <Button onClick={() => {
                            if (!deleteTarget) return
                            remove.mutate(deleteTarget.id, {
                                onSuccess() {
                                    setIsOpenDeleteModel(false); setDeleteTarget(null)
                                    setSuccessMessage(t("Customers_.deleteSuccess")); setIsOpenToast(true); invalidate()
                                },
                                onError() { setIsOpenDeleteModel(false) },
                            })
                        }}>{t("Suppliers.confirm")}</Button>
                    </div>
                </div>
            </Model>

            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div>
                <div className="flex items-center gap-x-3 mb-8">
                    {hasPermission(user, "customers", "create") &&
                        <Button onClick={() => setIsOpenAddModel(true)} variants="border" size="sm" iconOnly
                            leftIcon={<HugeiconsIcon size={16} icon={Plus} />} />}
                    <TableSettings<Customer> columns={columns}
                        columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                        grouping={grouping} setGrouping={setGrouping} />
                    <TableFilter<Customer> columns={columns}
                        columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                    <DebouncedInput fieldset={false} rounded="full" className="w-44"
                        placeholder={t("search") + "..."} value={globalFilter} onChange={setGlobalFilter} />
                </div>
                {errors.root?.server && <Text className="mb-3 text-error">{errors.root.server.message}</Text>}
                {data ? <Table<Customer>
                    columns={columns} data={data} tableKey="customers"
                    columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                    columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                    sorting={sorting} setSorting={setSorting}
                    grouping={grouping} setGrouping={setGrouping}
                    globalFilter={globalFilter} setGlobalFilter={setGlobalFilter}
                /> : <Text>{t("Orders_.emptyInbox")}</Text>}
            </div>
        </div>
    )
}
```

- [ ] **Step 2: Register the route**

Create `src/features/customers/customers.routes.ts`:

```ts
import type { RouteObject } from "react-router";
import { CustomersPage } from "./pages/CustomersPage";

export const customersRoutes: RouteObject[] = [
    {
        path: "customers",
        Component: CustomersPage,
    },
]
```

Create `src/features/customers/index.ts`:

```ts
export { customersRoutes } from "./customers.routes"
```

In `src/router.tsx`, add the import and spread it into the `/app` children:

```ts
import { customersRoutes } from "./features/customers";
```

```ts
                children:[
                    ...inventoryRoutes,
                    ...peoductsRoutes,
                    ...ordersRoutes,
                    ...customersRoutes
                ]
```

- [ ] **Step 3: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
npm run build
```

Expected: both clean.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/customers frontend/src/router.tsx
git commit -m "feat: add the customers page with manager approval

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: Role badge and the navigation restructure

**Files:**
- Modify: `src/components/Navigation.tsx`

**Interfaces:**
- Consumes: `customersRoutes` (Task 5); `authSlice.user.role`; the i18n keys from Task 4.
- Produces: nothing later tasks depend on.

The reference screenshot uses **static section headings**, not collapsible dropdowns. So the group toggles and their `useOpenMenu` instances go, replaced by a small muted label above each group's entries. The user-menu dropdown at the top stays exactly as it is.

**Do not change the Suppliers or Purchases entries** — same targets, same labels, same `active` logic. They are only moved under a heading.

- [ ] **Step 1: Add the section-label and greyed-entry helpers**

In `src/components/Navigation.tsx`, add these two small components directly above `const Navigation = forwardRef<...`:

```tsx
const SectionLabel = ({ children }: { children: React.ReactNode }) => (
  <Text className='px-2 pt-3 pb-1 text-xs opacity-60 select-none'>{children}</Text>
)

// Home, Employees and Settings have no backend yet. They are rendered so the
// shape of the app is visible, but they navigate nowhere - a nav entry that
// leads to a dead route is the bug this codebase keeps having to fix.
const ComingSoonEntry = ({ icon, label, hint }: { icon: any; label: string; hint: string }) => (
  <div className='w-full flex items-center gap-x-2 px-2 py-1.5 rounded-lg opacity-40 cursor-not-allowed select-none'
    aria-disabled='true' title={hint}>
    <HugeiconsIcon size={22} icon={icon} />
    <Text>{label}</Text>
  </div>
)
```

Add `Text` to the imports if it is not already there — it is imported in this file already; verify rather than assume.

- [ ] **Step 2: Show the role under the user's name**

Inside the user `<Button>` at the top, replace its children (currently `{user.first_name}`) with:

```tsx
             <span className='flex flex-col items-start leading-tight'>
               <Text>{user.first_name}</Text>
               <Text className='text-xs opacity-60'>{t(user.role)}</Text>
             </span>
```

`user.role` is already populated from the JWT's `role` claim, so this needs no API call.

- [ ] **Step 3: Replace the whole navigation body**

Replace everything between the closing `</div>` of the user-menu block and the closing `</div></div>` of the component — that is, every current group and top-level entry — with:

```tsx
        <ComingSoonEntry icon={DashboardSquare01Icon} label={t('home')} hint={t('comingSoon')} />

        <Button
          size='sm'
          className={`w-full justify-start`}
          variants='ghost'
          active={location.pathname.includes("/app/requests")}
          leftIcon={<HugeiconsIcon size={22} icon={RightToLeftListDashIcon} />}
          rightIcon={unreadCount > 0
            ? <span className="min-w-5 px-1.5 rounded-full text-xs bg-error text-dark-text-primary">{unreadCount}</span>
            : undefined}
          onClick={() => { navigarte("/app/requests", { state: { location: "requests" } }); }}
        >
          {t('requests')}
        </Button>

        <SectionLabel>{t('inventory')}</SectionLabel>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("inventory/categories")}
          leftIcon={<HugeiconsIcon size={22} icon={DashboardSquare01Icon} />}
          onClick={() => { navigarte("/app/inventory/categories/", { state: { location: "inventory" } }); }}>
          {t('categories')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("inventory/items")}
          leftIcon={<HugeiconsIcon size={22} icon={BoxIcon} />}
          onClick={() => { navigarte("/app/inventory/items", { state: { location: "inventory" } }); }}>
          {t('items')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname === "/app/products"}
          leftIcon={<HugeiconsIcon size={22} icon={BoxIcon} />}
          onClick={() => { navigarte("/app/products", { state: { location: "Products" } }); }}>
          {t('Products')}
        </Button>

        <SectionLabel>{t('inbound')}</SectionLabel>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname === "/app/orders"}
          leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
          onClick={() => { navigarte("/app/orders", { state: { location: "orders" } }); }}>
          {t('orders')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("/app/customers")}
          leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
          onClick={() => { navigarte("/app/customers", { state: { location: "customers" } }); }}>
          {t('customers')}
        </Button>

        <SectionLabel>{t('outbound')}</SectionLabel>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname === "/app/supplier"}
          leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
          onClick={() => { navigarte("/app/supplier", { state: { location: "Supplier" } }); }}>
          {t('suppliersList')}
        </Button>
        <Button size='sm' className={`w-full justify-start`} variants='ghost'
          active={location.pathname.includes("supplier/bills")}
          leftIcon={<HugeiconsIcon size={22} icon={Invoice03Icon} />}
          onClick={() => { navigarte("/app/supplier/bills", { state: { location: "supplierBills" } }); }}>
          {t('supplierBills')}
        </Button>

        <ComingSoonEntry icon={Trolley02Icon} label={t('employees')} hint={t('comingSoon')} />

        <SectionLabel>{t('preferences')}</SectionLabel>
        <ComingSoonEntry icon={Coupon01Icon} label={t('settings')} hint={t('comingSoon')} />
```

This removes the finance entry, which pointed at `/app/finance` — a route that has never existed. The finance group is added by the next plan, when its screens exist.

- [ ] **Step 4: Remove the now-unused group toggles**

The three group `useOpenMenu` calls (`isOpenSuppliers`, `isOpenWareHouse`, `isOpenOrders`) are no longer referenced. Delete those three lines. **Keep `isOpenUserButton`** — the user menu is still a dropdown.

`Dropdown` may now be imported but unused; if `tsc` reports it, remove that import too. Do the same for any icon import that is no longer referenced.

- [ ] **Step 5: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
npm run build
grep -rn "app/finance" src/
```

Expected: `tsc` and the build clean, and the grep prints nothing — the dead finance link is gone.

```bash
cd c:/Medware/frontemd
git add frontend/src/components/Navigation.tsx
git commit -m "feat: show the user's role and restructure the navigation into sections

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Manual verification

No browser automation exists here, so these are for the user:

- [ ] The nav shows the role under the name, and sections Inventory / Inbound / Outbound / Preferences.
- [ ] Home, Employees and Settings appear greyed and do nothing when clicked.
- [ ] As a salesman, creating a customer succeeds and the row shows "بانتظار الموافقة".
- [ ] As a manager, that customer appears in Requests; approving it flips the row to "معتمد" and the salesman sees the approval.
- [ ] Rejecting requires a reason, and the salesman sees the reason in Requests.
- [ ] As a salesman, an order can be raised for an approved customer but not a pending one.
- [ ] Suppliers and Purchases still go exactly where they did before.

## Self-review

**Spec coverage.** Part A: Tasks 1–3 (model, transitions, scoping, order validation, inbox rows). Part B: Task 6 Step 2. Part C: Task 6 Steps 1, 3, 4 — with the Finance group deliberately deferred to the next plan so no nav entry points at a route that does not exist. Parts D and E are out of this plan's scope by design.

**Placeholder scan.** No TBDs; every code step carries literal code. The greyed entries are a specified behaviour, not a placeholder.

**Type consistency.** `Customer.Status` members are identical across Tasks 1, 2 and 3. `_record_customer_transition(customer, from_status, actor, notes='')` is defined in Task 1 and called with that signature in Tasks 1 and 2. `notify(recipients, kind, target, message='')` matches the existing service. The frontend `Customer` type from Task 4 is the one Task 5 consumes, and the service names (`getCustomers`, `postCustomer`, `putCustomer`, `deleteCustomer`, `approveCustomer`, `rejectCustomer`) are defined once and used unchanged.

**Known risk.** Task 6 rewrites the body of `Navigation.tsx` wholesale. If any icon or import becomes unused, `tsc` fails with TS6133 — that is the intended signal, and Step 4 says to clear them.
