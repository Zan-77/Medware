# Role approval and user administration — design

**Status:** approved in brainstorming, 2026-09-05

## Why

The registration approval gate has been sitting commented out in `users/serializers.py` throughout development, so anyone can self-register as a `MANAGER` and be a real manager immediately. Turning it back on is only half the job: the gate blocks self-assignment at registration, but there is no way for a manager to grant a role or approve an account afterwards. `users/urls.py` exposes only role-*check* viewsets that return the requesting user. So re-enabling the gate without building the manager surface would leave every new account permanently stuck.

## The lockout this must avoid

There are exactly **two accounts** in the database. Both are `MANAGER`. Both have `is_verified = False`. There is **no superuser**.

Enable the gate as written and both accounts become guest-equivalent, with nobody left able to promote anyone — recoverable only through a Django shell. A bootstrap data migration verifying every existing account is therefore not a nicety; without it the first `migrate` bricks the environment.

## Decisions taken

| Decision | Choice | Reasoning |
|---|---|---|
| Where `is_verified` is enforced | **Server-side, for staff roles only** | The user's choice (a). Gating only the UI would leave an unverified manager with full API access via curl — the gate would stop nothing. Customers are exempt so the future storefront, where shoppers self-register, is not blocked behind manual approval |
| Which roles count as staff | `MANAGER`, `ACCOUNTANT`, `SALESMAN`, `WAREHOUSE_WORKER` | The same four already listed as `PRIVILEGED_ROLES` in `users/serializers.py`. The canonical set moves to `users/permissions.py` as `STAFF_ROLES`, and `serializers.py` imports it — two hand-maintained copies of "which roles are privileged" would drift, and the one that drifts silently is a security hole |
| What an unverified staff account can still do | Log in, refresh, log out, and read `/api/users/me/` | Enough for the UI to render "awaiting approval" and to notice the moment approval lands. Everything role-gated returns 403 |
| Existing accounts | A data migration sets `is_verified = True` for every row | They predate the gate. Without this the environment is unusable — see above |
| Source of truth for verification | The **database**, via `request.user.is_verified` | The access token lives 15 minutes, so a claim would lag approval by up to that long. Authorising off the row means access unlocks the instant a manager approves |
| `is_verified` in the JWT and `/api/users/me/` | Both, but `/api/users/me/` is authoritative | The claim gives the first render something to work with; the endpoint is what the pending screen re-checks |
| Manager guardrails | A manager may not change **their own** role or verification, and may not modify a **superuser** | One careless click otherwise locks the whole company out, which is exactly the state this spec exists to prevent |
| Audit | `audit.RequestTransition`, reused | Every other transition in this codebase writes one. A role change is a transition |

## Scope

**In:** re-enabling the three gate hooks; the bootstrap migration; verification enforcement in `RoleMethodPermission` and `HasRole`; `is_verified` on the JWT and `UserSerializer`; a manager-only user administration API; the Employees page; the pending-approval state.

**Out:** password reset, account deletion, invitations, email notification of approval, and any change to what each role may *do* — this governs who holds a role, not what the role permits.

---

## Part A — The gate

Three hooks are uncommented exactly as they stand in `users/serializers.py`:

1. `validate_role` on `RegisterSerializer` — a staff role may only be assigned by an authenticated manager or superuser. Everyone else self-registering with one gets a **400**.
2. `'is_verified'` in `RegisterSerializer.Meta.fields`.
3. In `create()`: `validated_data['is_verified'] = (validated_data.get('role') == User.Role.MANAGER)`.

**A correction to hook 3.** As written it self-verifies any account created with `role=MANAGER` — but `validate_role` now refuses that role to anyone who is not already a manager, so the only way through is a manager creating it, which is the intent. It stays as written; the two hooks are only safe together, which is why the comments say to uncomment them as a set.

`is_verified` is **never settable from the request body** — it is not in the writable fields, and there is already a test pinning that. That stays true.

## Part B — Enforcement

`users/permissions.py` becomes the single home of the staff-role set and gains one shared helper, used by both permission classes. `users/serializers.py` then imports `STAFF_ROLES` in place of its own `PRIVILEGED_ROLES` list, so there is exactly one definition of which roles are privileged:

```python
STAFF_ROLES = {'MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER'}


def staff_account_is_unverified(user):
    """A staff role only takes effect once a manager has approved the account.

    Customers are exempt: the storefront lets them self-register, and holding
    them behind manual approval would block it. Superusers bypass everything.
    """
    if getattr(user, 'is_superuser', False):
        return False
    return getattr(user, 'role', None) in STAFF_ROLES and not getattr(user, 'is_verified', False)
```

Both `HasRole.has_permission` and `RoleMethodPermission.has_permission` return `False` when it is true. Nothing else changes about either class.

What stays reachable for an unverified staff account, because none of it uses those classes: `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/auth/logout/`, `/api/auth/register/`, and `/api/users/me/`.

## Part C — User administration

```
GET   /api/users/manage/            Manager only. Every account.
PATCH /api/users/manage/<id>/       Manager only. `role` and `is_verified` only.
```

Registered under `manage/` rather than the bare `users/` prefix because `users/me/`, `users/roles/` and `users/access/…` already occupy that namespace and a router detail route would be an ambiguity waiting to happen.

`UserAdminSerializer` exposes `id`, `username`, `email`, `first_name`, `last_name`, `role`, `role_display`, `is_verified`, `is_staff`, `is_superuser`, `date_joined`. Only `role` and `is_verified` are writable; everything else is read-only.

**Guardrails, enforced in `perform_update`:**

- Modifying **yourself** → 403. A manager cannot demote or unverify their own account.
- Modifying a **superuser** → 403.

Both write an `audit.RequestTransition` row on success: `source_model='User'`, `source_id` the user's pk, `from_status`/`to_status` describing what changed (`role: SALESMAN -> MANAGER`, or `verified: False -> True`), `actor` the acting manager.

## Part D — Frontend

`is_verified` joins the user in the store, read from `/api/users/me/` rather than the token, because the token lags approval by up to its 15-minute lifetime.

**Pending state.** A signed-in staff account with `is_verified === false` sees an "awaiting manager approval" screen instead of the app, with a button that re-checks `/api/users/me/`. Customers never see it.

**Employees page** — `/app/employees`, manager only. A table of accounts showing username, email, role and verification state, with a role dropdown and a verify/unverify action per row. The **Employees** nav entry stops being greyed for managers and becomes a real link; it stays greyed for everyone else.

## Testing

The backend suite is the gate — 136 tests pass today. The frontend has no test runner; its gate is `tsc -b` and `npm run build`.

New backend tests:

- Self-registration with a staff role → **400**. *This is the rewrite of `test_self_registration_with_staff_role_is_currently_allowed`, which currently asserts 201 and carries a comment saying to update it when the gate returns.*
- Self-registration as a customer → 201, and the account is unverified.
- A manager creating a staff account → 201.
- An unverified salesman → 403 on a role-gated endpoint; the same account verified → 200.
- An unverified **customer** is unaffected on customer-readable endpoints.
- A superuser bypasses the verification check.
- `/api/users/me/` and token refresh still work for an unverified staff account.
- A manager lists users; a salesman gets 403 on the same endpoint.
- A manager changes another user's role, and an audit row records the change.
- A manager verifies another account, and it immediately passes a role-gated request.
- A manager modifying **their own** account → 403.
- A manager modifying a **superuser** → 403.

## Build order

1. Enforcement helper, the two permission classes, and the bootstrap data migration — together, because the migration is what stops the enforcement locking everyone out.
2. The gate hooks and the rewritten registration tests.
3. The user administration API with its guardrails and audit rows.
4. Frontend: `is_verified` in the store and the pending screen.
5. Frontend: the Employees page and its nav entry.

Steps 1 and 2 must land together in the same session — between them the environment is inconsistent, and step 1 alone with unverified accounts is the lockout this spec exists to prevent.
