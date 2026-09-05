# Role Approval and User Administration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the registration approval gate back on, enforce `is_verified` server-side for staff roles, and give managers a screen to grant roles and approve accounts.

**Architecture:** One shared helper in `users/permissions.py` decides whether a staff account is unapproved; both existing permission classes consult it, so enforcement lives in one place rather than being sprinkled across viewsets. A bootstrap data migration verifies every account that predates the gate — without it the first `migrate` locks the only two accounts out. Managers administer users through a small read/update viewset that writes an `audit.RequestTransition` on every change, the same audit trail every other transition in this codebase uses.

**Tech Stack:** Django 6.0.5, DRF 3.17.1, simplejwt 5.2.2, PostgreSQL. Frontend: React 19, React Router 8, TanStack Query 5, TanStack Table 9, react-hook-form 7, i18next (Arabic only), TypeScript 6, Vite 8.

**Spec:** `docs/superpowers/specs/2026-09-05-role-approval-and-user-administration-design.md`

## Global Constraints

- Backend lives at `c:/Medware/backend/Medware_Backend`; run `python manage.py …` from there in the **foreground** (the suite takes over three minutes — pass `timeout: 400000`).
- Backend commits go in the outer repo `c:/Medware` on branch `back`. Frontend commits go in the **separate nested repo** `c:/Medware/frontemd` on branch `frontend`.
- The backend suite is the gate for every backend task: `python manage.py test` must stay green (**136** tests pass before this plan starts).
- **There is no frontend test runner and none is to be added.** The frontend gate is `npx tsc -b` exiting 0 and `npm run build` succeeding.
- `is_verified` is **never settable from the request body on registration** — it is not in the writable fields, and a test already pins that.
- Verification is authorised from **the database** (`request.user.is_verified`), never from the JWT claim: the access token lives 15 minutes and would lag approval by that long.
- Only **staff roles** (`MANAGER`, `ACCOUNTANT`, `SALESMAN`, `WAREHOUSE_WORKER`) are gated by verification. Customers are exempt. Superusers bypass everything.
- These stay reachable for an unverified staff account: `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/auth/logout/`, `/api/auth/register/`, `/api/users/me/`.
- There is exactly one definition of which roles are privileged: `STAFF_ROLES` in `users/permissions.py`. `users/serializers.py` imports it.
- Every user-facing frontend string goes through `t(...)` with the key added to `src/i18n/ar.ts`.
- Reuse the existing frontend components — `Button`, `Model`, `Form`, `Table`, `TableFilter`, `TableSettings`, `DebouncedInput`, `Toast`, `Text`, `SelectInput`, `useOpenMenu`, `hasPermission`. No new UI or form library.
- Mixed line endings mean git prints `LF will be replaced by CRLF` warnings. Harmless.

---

### Task 1: Enforce verification for staff roles, and verify existing accounts

The migration and the enforcement must land together: there are two accounts in the database, both `MANAGER`, both `is_verified=False`, and no superuser. Enforcement without the backfill locks both out with no recovery but a Django shell.

**Files:**
- Modify: `users/permissions.py`, `users/serializers.py`
- Create: `users/migrations/<generated>_verify_existing_accounts.py`
- Test: `users/tests_security.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `users.permissions.STAFF_ROLES` (a set of the four role strings) and `users.permissions.staff_account_is_unverified(user) -> bool`. `HasRole` and `RoleMethodPermission` both refuse when it returns `True`.

- [ ] **Step 1: Write the failing test**

Append to `users/tests_security.py`:

```python
class StaffVerificationGateTests(TestCase):
    """A staff role only takes effect once a manager has approved the account.

    Gating only the UI would leave an unverified manager with full API access
    via curl, so the check lives in the permission classes.
    """

    def setUp(self):
        self.client = APIClient()
        self.unverified = User.objects.create_user(
            username='gate_slm', password='pass', role=User.Role.SALESMAN)
        self.verified = User.objects.create_user(
            username='gate_slm2', password='pass', role=User.Role.SALESMAN,
            is_verified=True)
        self.customer = User.objects.create_user(
            username='gate_cust', password='pass', role=User.Role.CUSTOMER)

    def test_an_unverified_staff_account_is_refused(self):
        self.client.force_authenticate(user=self.unverified)

        self.assertEqual(self.client.get('/api/products/products/').status_code, 403)

    def test_a_verified_staff_account_is_allowed(self):
        self.client.force_authenticate(user=self.verified)

        self.assertEqual(self.client.get('/api/products/products/').status_code, 200)

    def test_an_unverified_customer_is_unaffected(self):
        """The storefront lets customers self-register; holding them behind
        manual approval would block it."""
        self.client.force_authenticate(user=self.customer)

        self.assertEqual(self.client.get('/api/products/products/').status_code, 200)

    def test_a_superuser_bypasses_the_check(self):
        root = User.objects.create_superuser(
            username='gate_root', password='pass', email='root@example.com')
        self.client.force_authenticate(user=root)

        self.assertEqual(self.client.get('/api/products/products/').status_code, 200)

    def test_an_unverified_staff_account_can_still_read_its_own_profile(self):
        """Enough for the UI to render 'awaiting approval' and to notice the
        moment approval lands."""
        self.client.force_authenticate(user=self.unverified)

        resp = self.client.get('/api/users/me/')

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()['is_verified'])

    def test_an_unverified_staff_account_is_refused_by_the_role_check_views(self):
        """HasRole gates the /access/ endpoints and the role viewsets."""
        manager = User.objects.create_user(
            username='gate_mgr', password='pass', role=User.Role.MANAGER)
        self.client.force_authenticate(user=manager)

        self.assertEqual(self.client.get('/api/users/access/manager/').status_code, 403)

    def test_verifying_an_account_takes_effect_immediately(self):
        """Authorisation reads the row, not the 15-minute token claim."""
        self.client.force_authenticate(user=self.unverified)
        self.assertEqual(self.client.get('/api/products/products/').status_code, 403)

        self.unverified.is_verified = True
        self.unverified.save(update_fields=['is_verified'])

        self.assertEqual(self.client.get('/api/products/products/').status_code, 200)


class ExistingAccountsBackfillTests(TestCase):
    def test_the_staff_role_set_is_defined_once(self):
        """Two hand-maintained copies of "which roles are privileged" drift,
        and the one that drifts silently is a security hole."""
        from users import serializers as user_serializers
        from users.permissions import STAFF_ROLES

        self.assertIs(user_serializers.STAFF_ROLES, STAFF_ROLES)
        self.assertEqual(STAFF_ROLES,
                         {'MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER'})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test users.tests_security.StaffVerificationGateTests`
Expected: FAIL — the unverified salesman gets 200, and `/api/users/me/` has no `is_verified` key.

- [ ] **Step 3: Add the staff-role set and the helper**

In `users/permissions.py`, insert directly below the `try/except` import block:

```python
# The single definition of which roles carry staff privileges. `serializers.py`
# imports this rather than keeping its own copy - two hand-maintained lists of
# "which roles are privileged" drift, and the one that drifts is a hole.
STAFF_ROLES = {'MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER'}


def staff_account_is_unverified(user):
    """True when this account holds a staff role a manager has not approved.

    Customers are exempt: the storefront lets them self-register, and holding
    them behind manual approval would block it. Superusers bypass entirely.
    """
    if getattr(user, 'is_superuser', False):
        return False
    return (
        getattr(user, 'role', None) in STAFF_ROLES
        and not getattr(user, 'is_verified', False)
    )
```

- [ ] **Step 4: Wire it into both permission classes**

Replace `HasRole.has_permission`:

```python
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if staff_account_is_unverified(request.user):
            return False
        return request.user.role in self.allowed_roles
```

In `RoleMethodPermission.has_permission`, add the check immediately after the superuser bypass, so a superuser still short-circuits first:

```python
        if getattr(request.user, 'is_superuser', False):
            return True

        # A staff role does not take effect until a manager approves the
        # account. Checked against the row, not the token claim.
        if staff_account_is_unverified(request.user):
            return False
```

- [ ] **Step 5: Make `serializers.py` import the one definition**

In `users/serializers.py`, replace the whole `PRIVILEGED_ROLES = { ... }` block — and the comment paragraph above it that says the gate is disabled — with:

```python
# Roles that carry staff privileges. Defined once in permissions.py, which is
# also where the verification check that uses them lives.
#
# APPROVAL MODEL: anyone may register, but only a manager may hand out a staff
# role directly, and a staff account holds no privileges until a manager sets
# `is_verified`. Enforced in users/permissions.py, not only in the UI.
from .permissions import STAFF_ROLES
```

Move that import up with the other imports at the top of the file if your linter prefers; it must not be inside a function.

- [ ] **Step 6: Expose `is_verified` on `/api/users/me/`**

In `users/serializers.py`, in `UserSerializer.Meta.fields`, replace the commented line with a real one:

```python
            'is_verified',
```

- [ ] **Step 7: Generate and write the bootstrap migration**

```bash
python manage.py makemigrations users --empty --name verify_existing_accounts
```

Fill the generated file in:

```python
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
        ('users', '<the latest existing users migration>'),
    ]

    operations = [
        migrations.RunPython(verify_existing_accounts, noop),
    ]
```

Replace `<the latest existing users migration>` with whatever `makemigrations` put there — it fills the dependency in automatically, so usually you only replace the body.

- [ ] **Step 8: Migrate and run the tests**

```bash
python manage.py migrate
python manage.py test users
```

Expected: the migration applies, and the `users` tests pass.

- [ ] **Step 9: Run the whole suite and commit**

Some existing tests create staff users without `is_verified=True` and will now get 403 where they expected 200. **Fix each by adding `is_verified=True` to the account's creation**, never by weakening an assertion. Report every test you changed.

```bash
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/users
git commit -m "feat: a staff role takes effect only once a manager verifies the account

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Turn the registration gate back on

**Files:**
- Modify: `users/serializers.py`
- Test: `users/tests_security.py`

**Interfaces:**
- Consumes: `STAFF_ROLES` from Task 1.
- Produces: registration refuses a staff role to anyone who is not already a manager (400), and every new account except a manager-created one starts unverified.

- [ ] **Step 1: Rewrite the test that pins the insecure behaviour**

`users/tests_security.py` contains `test_self_registration_with_staff_role_is_currently_allowed`, which asserts **201** and carries the comment *"If this is now 400 the approval gate is back on - update this test."* This is that moment. Replace that whole test method with:

```python
    def test_self_registration_with_a_staff_role_is_refused(self):
        """The approval gate: a staff role may only be granted by a manager."""
        resp = self.client.post('/api/auth/register/', {
            'username': 'escalate', 'email': 'escalate@example.com',
            'first_name': 'E', 'last_name': 'S',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'MANAGER',
        }, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertIn('role', resp.json())
        self.assertFalse(User.objects.filter(username='escalate').exists())

    def test_self_registration_as_a_customer_is_allowed_but_unverified(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'shopper', 'email': 'shopper@example.com',
            'first_name': 'S', 'last_name': 'H',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'CUSTOMER',
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        created = User.objects.get(username='shopper')
        self.assertEqual(created.role, 'CUSTOMER')
        self.assertFalse(created.is_verified)

    def test_a_manager_may_create_a_staff_account(self):
        manager = User.objects.create_user(
            username='reg_mgr', password='pass', role=User.Role.MANAGER,
            is_verified=True)
        self.client.force_authenticate(user=manager)

        resp = self.client.post('/api/auth/register/', {
            'username': 'new_salesman', 'email': 'ns@example.com',
            'first_name': 'N', 'last_name': 'S',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'SALESMAN',
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(username='new_salesman').role, 'SALESMAN')

    def test_is_verified_is_still_not_settable_from_the_request_body(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'selfverify', 'email': 'sv@example.com',
            'first_name': 'S', 'last_name': 'V',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'CUSTOMER', 'is_verified': True,
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        self.assertFalse(User.objects.get(username='selfverify').is_verified)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test users.tests_security`
Expected: FAIL — self-registration with `MANAGER` still returns 201.

- [ ] **Step 3: Uncomment the gate on `RegisterSerializer`**

In `users/serializers.py`, replace the commented `validate_role` block — the whole `# --- manager approval gate (DISABLED …)` comment paragraph and the commented method — with the live method:

```python
    def validate_role(self, value):
        """A staff role may only be granted directly by a manager.

        Everyone else may register, but lands unverified and holds no
        privileges until a manager approves the account.
        """
        if value not in STAFF_ROLES:
            return value
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        if actor is not None and actor.is_authenticated and (
            actor.is_superuser or actor.role == User.Role.MANAGER
        ):
            return value
        raise serializers.ValidationError(
            'You are not allowed to assign this role. Staff accounts must be '
            'created by a manager.'
        )
```

- [ ] **Step 4: Turn on the two remaining hooks**

In `RegisterSerializer.Meta.fields`, replace the commented line with:

```python
            'is_verified',
```

In `create()`, replace the commented block with the live assignment:

```python
        # Only a manager can reach this with a staff role (see validate_role),
        # so a manager-created manager is trusted; everything else waits for
        # approval.
        validated_data['is_verified'] = (
            validated_data.get('role') == User.Role.MANAGER
        )
```

- [ ] **Step 5: Put `is_verified` in the token claims**

In `build_tokens_for_user`, replace the commented claim with a live one:

```python
    refresh['is_verified'] = user.is_verified
```

Keep the comment above it, amended to say the claim is for first render only and that `/api/users/me/` is authoritative:

```python
    # The frontend decodes this for its first render. It is a snapshot: the
    # access token lives 15 minutes, so after a manager approves an account
    # this claim lags. /api/users/me/ is the authoritative source.
```

- [ ] **Step 6: Run the tests, the whole suite, and commit**

```bash
python manage.py test users
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/users
git commit -m "feat: re-enable the manager approval gate on registration

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: The manager's user administration API

**Files:**
- Modify: `users/serializers.py`, `users/views.py`, `users/urls.py`
- Test: `users/tests_security.py`

**Interfaces:**
- Consumes: `IsManager` (now verification-aware, Task 1).
- Produces: `GET /api/users/manage/` and `PATCH /api/users/manage/<id>/`, manager only, with `role` and `is_verified` the only writable fields.

- [ ] **Step 1: Write the failing test**

Append to `users/tests_security.py`:

```python
class UserAdministrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            username='adm_mgr', password='pass', role=User.Role.MANAGER, is_verified=True)
        self.salesman = User.objects.create_user(
            username='adm_slm', password='pass', role=User.Role.SALESMAN)

    def test_a_manager_lists_every_account(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.get('/api/users/manage/')

        self.assertEqual(resp.status_code, 200)
        usernames = {row['username'] for row in resp.json()}
        self.assertEqual(usernames, {'adm_mgr', 'adm_slm'})

    def test_the_list_carries_the_role_and_verification_state(self):
        self.client.force_authenticate(user=self.manager)

        row = next(r for r in self.client.get('/api/users/manage/').json()
                   if r['username'] == 'adm_slm')

        self.assertEqual(row['role'], 'SALESMAN')
        self.assertFalse(row['is_verified'])
        self.assertIn('role_display', row)

    def test_a_salesman_cannot_list_accounts(self):
        self.salesman.is_verified = True
        self.salesman.save(update_fields=['is_verified'])
        self.client.force_authenticate(user=self.salesman)

        self.assertEqual(self.client.get('/api/users/manage/').status_code, 403)

    def test_a_manager_verifies_an_account_and_it_works_immediately(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/users/manage/{self.salesman.pk}/',
                                 {'is_verified': True}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.salesman.refresh_from_db()
        self.assertTrue(self.salesman.is_verified)

        promoted = APIClient()
        promoted.force_authenticate(user=self.salesman)
        self.assertEqual(promoted.get('/api/products/products/').status_code, 200)

    def test_a_manager_changes_a_role_and_it_is_audited(self):
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/users/manage/{self.salesman.pk}/',
                                 {'role': 'ACCOUNTANT'}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.salesman.refresh_from_db()
        self.assertEqual(self.salesman.role, 'ACCOUNTANT')
        transition = RequestTransition.objects.get(
            source_model='User', source_id=str(self.salesman.pk))
        self.assertIn('SALESMAN', transition.from_status)
        self.assertIn('ACCOUNTANT', transition.to_status)
        self.assertEqual(transition.actor, self.manager)

    def test_a_manager_cannot_change_their_own_account(self):
        """One careless click otherwise locks the company out."""
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/users/manage/{self.manager.pk}/',
                                 {'role': 'SALESMAN'}, format='json')

        self.manager.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.manager.role, 'MANAGER')

    def test_a_manager_cannot_modify_a_superuser(self):
        root = User.objects.create_superuser(
            username='adm_root', password='pass', email='r@example.com')
        self.client.force_authenticate(user=self.manager)

        resp = self.client.patch(f'/api/users/manage/{root.pk}/',
                                 {'role': 'CUSTOMER'}, format='json')

        root.refresh_from_db()
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(root.is_superuser)

    def test_username_and_password_are_not_writable_here(self):
        self.client.force_authenticate(user=self.manager)

        self.client.patch(f'/api/users/manage/{self.salesman.pk}/',
                          {'username': 'renamed'}, format='json')

        self.salesman.refresh_from_db()
        self.assertEqual(self.salesman.username, 'adm_slm')

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/users/manage/').status_code, 401)
```

Add `from audit.models import RequestTransition` to the imports at the top of `users/tests_security.py` if it is not already there — verify rather than assume.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python manage.py test users.tests_security.UserAdministrationTests`
Expected: FAIL — 404, the URL does not exist.

- [ ] **Step 3: Add the admin serializer**

Append to `users/serializers.py`:

```python
class UserAdminSerializer(serializers.ModelSerializer):
    """The manager's view of an account. Only `role` and `is_verified` move."""

    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'is_verified',
            'is_staff', 'is_superuser', 'date_joined',
        ]
        read_only_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role_display', 'is_staff', 'is_superuser', 'date_joined',
        ]
```

- [ ] **Step 4: Add the viewset**

In `users/views.py`, add these imports if missing — check what is already there:

```python
from rest_framework import mixins
from rest_framework.exceptions import PermissionDenied

from audit.models import RequestTransition

from .serializers import UserAdminSerializer
```

Then append the viewset:

```python
class UserAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Manager-only account administration: grant a role, approve an account.

    No create and no destroy - accounts are made by registering, and deleting
    one would cascade into the orders and customers that reference it.
    """

    queryset = User.objects.all().order_by('username')
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def perform_update(self, serializer):
        target = serializer.instance
        actor = self.request.user

        # Both guards exist to stop one careless click locking the company out.
        if target.pk == actor.pk:
            raise PermissionDenied(
                'You cannot change your own role or verification.')
        if target.is_superuser:
            raise PermissionDenied('A superuser account cannot be changed here.')

        before_role, before_verified = target.role, target.is_verified
        user = serializer.save()

        if user.role == before_role and user.is_verified == before_verified:
            return

        changes = []
        if user.role != before_role:
            changes.append(f'role: {before_role} -> {user.role}')
        if user.is_verified != before_verified:
            changes.append(f'verified: {before_verified} -> {user.is_verified}')

        RequestTransition.objects.create(
            source_model='User',
            source_id=str(user.pk),
            from_status=f'role={before_role},verified={before_verified}',
            to_status=f'role={user.role},verified={user.is_verified}',
            actor=actor,
            actor_role=getattr(actor, 'role', ''),
            notes='; '.join(changes),
        )
```

`viewsets`, `permissions` and `IsManager` are already imported in this module — verify rather than assume.

- [ ] **Step 5: Register the route**

In `users/urls.py`, add to the router registrations:

```python
router.register('users/manage', views.UserAdminViewSet, basename='user-admin')
```

The prefix is `users/manage` rather than the bare `users` because `users/me/`, `users/roles/` and `users/access/…` already occupy that namespace and a router detail route there would be an ambiguity waiting to happen. Those explicit paths are listed before `include(router.urls)`, so they continue to win.

- [ ] **Step 6: Run the tests, the whole suite, and commit**

```bash
python manage.py test users
python manage.py test
cd c:/Medware
git add backend/Medware_Backend/users
git commit -m "feat: manager-only user administration with audited role changes

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: The pending-approval state in the app

**Files:**
- Create: `src/features/auth/pages/PendingApprovalPage.tsx`
- Modify: `src/features/auth/types/users.ts`, `src/features/auth/authSlice.ts`, `src/features/auth/services/auth.service.ts`, `src/features/auth/utility/decodeAccessToken.ts`, `src/layouts/appLayout.tsx`, `src/i18n/ar.ts`

**Interfaces:**
- Consumes: `GET /api/users/me/` now returning `is_verified` (Task 1).
- Produces: `getCurrentUser()` in `auth.service.ts` returning the `/api/users/me/` payload; `is_verified` on the store's user.

- [ ] **Step 1: Add `is_verified` to the user type and the store default**

In `src/features/auth/types/users.ts`, add to the user type:

```ts
    is_verified?: boolean
```

In `src/features/auth/authSlice.ts`, add `is_verified: false` to the initial `user` object so the shape is complete from the first render.

- [ ] **Step 2: Read the claim, and add the authoritative fetch**

In `src/features/auth/utility/decodeAccessToken.ts`, add to `JwtPayload`:

```ts
is_verified?: boolean
```

In `src/features/auth/services/auth.service.ts`, add:

```ts
export interface CurrentUser {
    id: string
    username: string
    email: string
    role: string
    role_display: string
    is_verified: boolean
    is_staff: boolean
    is_superuser: boolean
}

// The token claim is a 15-minute-old snapshot, so after a manager approves an
// account it lags. This endpoint is the authoritative answer.
export async function getCurrentUser(): Promise<CurrentUser> {
    const res = await ax.get<CurrentUser>("/users/me/")
    return res.data
}
```

- [ ] **Step 3: Write the pending screen**

Create `src/features/auth/pages/PendingApprovalPage.tsx`:

```tsx
import { useQueryClient } from "@tanstack/react-query"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import Text from "../../../components/Text"

export const PendingApprovalPage = () => {
    const { t } = useTranslation()
    const queryClient = useQueryClient()

    return (
        <div className="flex flex-col items-center justify-center gap-y-4 p-10">
            <Text weight="medium">{t("Pending.title")}</Text>
            <Text>{t("Pending.body")}</Text>
            <Button onClick={() => queryClient.invalidateQueries({ queryKey: ["me"] })}>
                {t("Pending.recheck")}
            </Button>
        </div>
    )
}
```

- [ ] **Step 4: Gate the app shell on it**

In `src/layouts/appLayout.tsx`, add these imports:

```tsx
import { useQuery } from '@tanstack/react-query'
import { getCurrentUser } from '../features/auth/services/auth.service'
import { PendingApprovalPage } from '../features/auth/pages/PendingApprovalPage'
```

Inside the component, above the existing `useLayoutEffect`, add:

```tsx
    // Authoritative: the token claim lags approval by up to its 15-minute life.
    const { data: me } = useQuery({ queryKey: ["me"], queryFn: getCurrentUser })
    const STAFF_ROLES = ["MANAGER", "ACCOUNTANT", "SALESMAN", "WAREHOUSE_WORKER"]
    const awaitingApproval = Boolean(
        me && STAFF_ROLES.includes(me.role) && !me.is_verified && !me.is_superuser
    )
```

Then, in the returned JSX, replace `<Outlet />` with:

```tsx
                    {awaitingApproval ? <PendingApprovalPage /> : <Outlet />}
```

Leave the navigation rendered — a pending user can still sign out.

- [ ] **Step 5: Add the Arabic strings**

In `src/i18n/ar.ts`, add after the `comingSoon` key:

```ts
    Pending: {
        title: "الحساب بانتظار الموافقة",
        body: "تم إنشاء حسابك ويحتاج إلى موافقة المدير قبل استخدام النظام.",
        recheck: "تحقق مرة أخرى"
    },
```

- [ ] **Step 6: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
npm run build
```

Expected: both clean.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/auth frontend/src/layouts/appLayout.tsx frontend/src/i18n/ar.ts
git commit -m "feat: show an awaiting-approval screen for unverified staff

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: The Employees page

**Files:**
- Create: `src/features/employees/types/employees.ts`, `src/features/employees/services/employees.service.ts`, `src/features/employees/pages/EmployeesPage.tsx`, `src/features/employees/employees.routes.ts`, `src/features/employees/index.ts`
- Modify: `src/router.tsx`, `src/components/Navigation.tsx`, `src/features/auth/Permissions.tsx`, `src/i18n/ar.ts`

**Interfaces:**
- Consumes: `GET /api/users/manage/` and `PATCH /api/users/manage/<id>/` (Task 3).
- Produces: `employeesRoutes` exported from `src/features/employees/index.ts`, registering `/app/employees`.

**UI constraint:** mirror `src/features/customers/pages/CustomersPage.tsx` — the same toolbar, `Table`, `Toast`, `useOpenMenu` and `hasPermission` gating. Read it before writing this.

- [ ] **Step 1: Write the type and service**

Create `src/features/employees/types/employees.ts`:

```ts
// Mirrors users.serializers.UserAdminSerializer. Only `role` and
// `is_verified` are writable server-side.
export interface Employee {
    id: string
    username: string
    email: string
    first_name: string
    last_name: string
    role: string
    role_display: string
    is_verified: boolean
    is_staff: boolean
    is_superuser: boolean
    date_joined: string
}
```

Create `src/features/employees/services/employees.service.ts`:

```ts
import ax from "../../../services/api"
import type { Employee } from "../types/employees"

const employeesUrl = "/users/manage/"

export const getEmployees = async (): Promise<Employee[]> => {
	const res = await ax.get<Employee[]>(employeesUrl)
	return res.data
}

// The server refuses a manager changing their own account or a superuser's,
// and ignores every field but these two.
export const patchEmployee = async (
	id: string,
	data: { role?: string; is_verified?: boolean },
): Promise<Employee> => {
	const res = await ax.patch<Employee>(`${employeesUrl}${id}/`, data)
	return res.data
}
```

- [ ] **Step 2: Add the permission key**

In `src/features/auth/Permissions.tsx`, add to the `Permissions` type after `customerApproval`:

```ts
    employees: {
        dataType: Employee
        actions: Actions
    }
```

with the import:

```ts
import type { Employee } from "../employees/types/employees"
```

Then add the key to **every** role block. `MANAGER`:

```ts
        employees: { read: true, create: false, update: true, delete: false },
```

`GUEST`, `CUSTOMER`, `ACCOUNTANT`, `SALESMAN` and `WAREHOUSE_WORKER`:

```ts
        employees: { read: false, create: false, update: false, delete: false },
```

- [ ] **Step 3: Write the page**

Create `src/features/employees/pages/EmployeesPage.tsx`:

```tsx
import { HugeiconsIcon } from "@hugeicons/react"
import { CheckmarkCircle01Icon } from "@hugeicons/core-free-icons"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { filterFn_includesString, type ColumnDef, type ColumnFiltersState, type ColumnVisibilityState, type GroupingState, type SortingState, type TableFeatures } from "@tanstack/react-table"
import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import Button from "../../../components/Button"
import DebouncedInput from "../../../components/DebouncedInput"
import SelectInput from "../../../components/SelectInput"
import { Table } from "../../../components/Table"
import TableFilter from "../../../components/TableFilter"
import TableSettings from "../../../components/TableSettings"
import Text from "../../../components/Text"
import Toast from "../../../components/Toast"
import useOpenMenu from "../../../hooks/useOpenMenu"
import { useBoundStore } from "../../../store/useBoundStore"
import { hasPermission } from "../../auth"
import { getEmployees, patchEmployee } from "../services/employees.service"
import type { Employee } from "../types/employees"

const ASSIGNABLE_ROLES = ["MANAGER", "ACCOUNTANT", "SALESMAN", "WAREHOUSE_WORKER", "CUSTOMER", "GUEST"]

export const EmployeesPage = () => {
    const user = useBoundStore(state => state.authSlice.user)
    const { t } = useTranslation()
    const queryClient = useQueryClient()
    const { isOpen: isOpenToast, setIsOpen: setIsOpenToast, ref: toastRef } = useOpenMenu()

    const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
    const [sorting, setSorting] = useState<SortingState>([])
    const [grouping, setGrouping] = useState<GroupingState>([])
    const [globalFilter, setGlobalFilter] = useState('')
    const [columnVisibility, setColumnVisibility] = useState<ColumnVisibilityState>({
        username: true, role: true, is_verified: true,
    })
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const [errorMessage, setErrorMessage] = useState<string | null>(null)

    const { data } = useQuery({ queryKey: ["employees"], queryFn: getEmployees })

    const update = useMutation({
        mutationFn: ({ id, changes }: { id: string; changes: { role?: string; is_verified?: boolean } }) =>
            patchEmployee(id, changes),
        onSuccess() {
            setErrorMessage(null)
            setSuccessMessage(t("Employees_.updateSuccess"))
            setIsOpenToast(true)
            queryClient.invalidateQueries({ queryKey: ["employees"] })
            // The signed-in user's own verification may have changed elsewhere.
            queryClient.invalidateQueries({ queryKey: ["me"] })
        },
        onError() {
            // 403 when a manager targets themselves or a superuser.
            setErrorMessage(t("Employees_.serverError"))
        },
    })

    useEffect(() => {
        if (!isOpenToast) return
        const id = window.setTimeout(() => { setIsOpenToast(false); setSuccessMessage(null) }, 3000)
        return () => window.clearTimeout(id)
    }, [isOpenToast, setIsOpenToast])

    // Mirrors the server guards: a manager may not change their own account or
    // a superuser's, so those rows render read-only rather than failing on click.
    const canEdit = (row: Employee) =>
        hasPermission(user, "employees", "update") &&
        String(row.id) !== String(user.id) &&
        !row.is_superuser

    const columns: Array<ColumnDef<TableFeatures, Employee>> = [
        {
            meta: { filterVariants: "value" }, id: "username", enableSorting: true,
            header: t("name"), accessorKey: "username", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "email", enableSorting: true,
            header: t("email"), accessorKey: "email", filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "role", enableSorting: true,
            header: t("role"),
            accessorFn: (row) => t(row.role),
            cell: ({ row }) => canEdit(row.original)
                ? <SelectInput
                    value={row.original.role}
                    onChange={(event) => update.mutate({
                        id: row.original.id, changes: { role: event.target.value },
                    })}>
                    {ASSIGNABLE_ROLES.map((role) => (
                        <option key={role} value={role}>{t(role)}</option>
                    ))}
                </SelectInput>
                : t(row.original.role),
            filterFn: filterFn_includesString,
        },
        {
            meta: { filterVariants: "value" }, id: "is_verified", enableSorting: true,
            header: t("Employees_.verified"),
            accessorFn: (row) => row.is_verified ? t("Employees_.yes") : t("Employees_.no"),
            cell: ({ row }) => canEdit(row.original)
                ? <Button size="xs" variants="ghost"
                    className={row.original.is_verified ? "dark:text-error text-error" : "dark:text-accent-medium text-accent-dark"}
                    onClick={() => update.mutate({
                        id: row.original.id, changes: { is_verified: !row.original.is_verified },
                    })}>
                    {row.original.is_verified ? t("Employees_.revoke") : t("Employees_.verify")}
                </Button>
                : (row.original.is_verified ? t("Employees_.yes") : t("Employees_.no")),
            filterFn: filterFn_includesString,
        },
    ]

    return (
        <div>
            <Toast onClick={() => { setIsOpenToast(false); setSuccessMessage(null) }} isOpen={isOpenToast} ref={toastRef}>
                {successMessage && <div className="flex items-center gap-x-2">
                    <HugeiconsIcon className="*:fill-ok *:stroke-white" size={24} icon={CheckmarkCircle01Icon} />
                    <Text>{successMessage}</Text>
                </div>}
            </Toast>

            <div className="flex items-center gap-x-3 mb-8">
                <TableSettings<Employee> columns={columns}
                    columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                    grouping={grouping} setGrouping={setGrouping} />
                <TableFilter<Employee> columns={columns}
                    columnFilters={columnFilters} setColumnFilters={setColumnFilters} />
                <DebouncedInput fieldset={false} rounded="full" className="w-44"
                    placeholder={t("search") + "..."} value={globalFilter} onChange={setGlobalFilter} />
            </div>

            {errorMessage && <Text className="mb-3 text-error">{errorMessage}</Text>}

            {data ? <Table<Employee>
                columns={columns} data={data} tableKey="employees"
                columnFilters={columnFilters} setColumnFilters={setColumnFilters}
                columnVisibility={columnVisibility} setColumnVisibility={setColumnVisibility}
                sorting={sorting} setSorting={setSorting}
                grouping={grouping} setGrouping={setGrouping}
                globalFilter={globalFilter} setGlobalFilter={setGlobalFilter}
            /> : <Text>{t("Orders_.emptyInbox")}</Text>}
        </div>
    )
}
```

- [ ] **Step 4: Register the route**

Create `src/features/employees/employees.routes.ts`:

```ts
import type { RouteObject } from "react-router";
import { EmployeesPage } from "./pages/EmployeesPage";

export const employeesRoutes: RouteObject[] = [
    {
        path: "employees",
        Component: EmployeesPage,
    },
]
```

Create `src/features/employees/index.ts`:

```ts
export { employeesRoutes } from "./employees.routes"
```

In `src/router.tsx`, add the import and spread it into the `/app` children:

```ts
import { employeesRoutes } from "./features/employees";
```

```ts
                    ...customersRoutes,
                    ...employeesRoutes
```

- [ ] **Step 5: Make the Employees nav entry real for managers**

In `src/components/Navigation.tsx`, replace the greyed Employees entry — the line reading `<ComingSoonEntry icon={Trolley02Icon} label={t('employees')} hint={t('comingSoon')} />` — with:

```tsx
        {hasPermission(user, "employees", "read")
          ? <Button size='sm' className={`w-full justify-start`} variants='ghost'
              active={location.pathname.includes("/app/employees")}
              leftIcon={<HugeiconsIcon size={22} icon={Trolley02Icon} />}
              onClick={() => { navigarte("/app/employees", { state: { location: "employees" } }); }}>
              {t('employees')}
            </Button>
          : <ComingSoonEntry icon={Trolley02Icon} label={t('employees')} hint={t('comingSoon')} />}
```

Add the import if missing:

```tsx
import { hasPermission } from '../features/auth'
```

`user` is already read from the store in this component — verify rather than assume.

- [ ] **Step 6: Add the Arabic strings**

In `src/i18n/ar.ts`, add after the `Pending` group:

```ts
    role: "الدور",
    email: "البريد الإلكتروني",
    Employees_: {
        verified: "موثّق",
        yes: "نعم",
        no: "لا",
        verify: "توثيق",
        revoke: "إلغاء التوثيق",
        updateSuccess: "تم تحديث الحساب",
        serverError: "لا يمكن تعديل هذا الحساب."
    },
```

- [ ] **Step 7: Verify and commit**

```bash
cd c:/Medware/frontemd/frontend
npx tsc -b
npm run build
```

Expected: both clean.

```bash
cd c:/Medware/frontemd
git add frontend/src/features/employees frontend/src/router.tsx frontend/src/components/Navigation.tsx frontend/src/features/auth/Permissions.tsx frontend/src/i18n/ar.ts
git commit -m "feat: add the employees page for managing roles and approvals

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Manual verification

No browser automation exists here, so these are for the user:

- [ ] Both existing manager accounts still work after `migrate` — the backfill verified them.
- [ ] Registering a new account with role `MANAGER` is refused with a message about staff accounts.
- [ ] Registering as a customer succeeds.
- [ ] A manager creates a salesman account from the register form while signed in; it is created unverified.
- [ ] That salesman signs in and sees "الحساب بانتظار الموافقة" instead of the app.
- [ ] The manager opens Employees, verifies that account, and the salesman's "check again" lets them straight in.
- [ ] The manager's own row shows a plain role and no verify button.

## Self-review

**Spec coverage.** Part A (the gate) → Task 2. Part B (enforcement, one `STAFF_ROLES` definition, the reachable-endpoint list) → Task 1. Part C (the admin API, both guardrails, the audit row) → Task 3. Part D (`is_verified` in the store, the pending screen, the Employees page and its nav entry) → Tasks 4 and 5. The bootstrap migration is Task 1 Step 7. Every spec requirement has a task.

**Placeholder scan.** No TBDs; every code step carries literal code. Task 1 Step 9's instruction to repair existing tests is a real instruction with a stated rule — fix the fixture, never the assertion — not a vague gesture.

**Type consistency.** `STAFF_ROLES` is the same set in Tasks 1, 2 and 4 (the frontend re-lists the four strings because it cannot import Python — that is the one deliberate duplication, and the pending screen is the only consumer). `staff_account_is_unverified(user)` is defined once and called from both permission classes. `UserAdminSerializer`'s field list in Task 3 is exactly what the frontend `Employee` type mirrors in Task 5. `getCurrentUser()` and the `["me"]` query key are introduced in Task 4 and reused by Task 5's invalidation.

**Known risk.** Task 1 will break existing tests that create staff users without `is_verified=True`. That is expected and the step says to fix the fixtures rather than the assertions — but it could touch a number of files across `orders`, `customers`, `inventory` and `products`, and a careless fix there would silently weaken an unrelated security test.
