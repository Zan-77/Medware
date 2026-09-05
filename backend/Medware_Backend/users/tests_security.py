"""Regression tests for the security fixes.

Each test here corresponds to a hole that was demonstrably exploitable before
the fix, so a failure means the hole is back. Picked up automatically by
`python manage.py test`.
"""

from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import User
from orders.models import OrderRequest
from audit.models import AuditLog, RequestTransition
from products.models import Product


class SecurityRegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            username='sec_cust', email='sec_cust@example.com', password='pass1234',
            role=User.Role.CUSTOMER)
        self.other_customer = User.objects.create_user(
            username='sec_other', email='sec_other@example.com', password='pass1234',
            role=User.Role.CUSTOMER)
        self.manager = User.objects.create_user(
            username='sec_mgr', email='sec_mgr@example.com', password='pass1234',
            role=User.Role.MANAGER, is_verified=True)

    # --- registration policy ------------------------------------------------
    # The manager-approval gate is ON. Anyone may REGISTER requesting any role -
    # signup never fails on the role, so the UI can show "awaiting approval"
    # rather than an error. The role simply does nothing until a manager
    # verifies the account. Verification is conferred by the ACTOR creating the
    # account, never by the role requested.
    def test_self_registration_with_a_staff_role_succeeds_but_is_unverified(self):
        """Signup must not fail on the role - the UI shows "awaiting approval".

        The role is inert until a manager verifies the account, so letting the
        request through costs nothing and gives the person somewhere to land.
        """
        resp = self.client.post('/api/auth/register/', {
            'username': 'escalate', 'email': 'escalate@example.com',
            'first_name': 'E', 'last_name': 'S',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'MANAGER',
        }, format='json')

        self.assertEqual(resp.status_code, 201)
        created = User.objects.get(username='escalate')
        self.assertEqual(created.role, 'MANAGER')
        self.assertFalse(
            created.is_verified,
            'Self-registering as MANAGER must never confer verification - that '
            'would bypass the entire gate with a dropdown.')

    def test_a_self_registered_staff_account_can_do_nothing_until_verified(self):
        """The role being inert is what makes the permissive signup safe."""
        self.client.post('/api/auth/register/', {
            'username': 'inert', 'email': 'inert@example.com',
            'first_name': 'I', 'last_name': 'N',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'MANAGER',
        }, format='json')

        pending = APIClient()
        pending.force_authenticate(user=User.objects.get(username='inert'))
        self.assertEqual(pending.get('/api/products/products/').status_code, 403)

    def test_an_unverified_manager_cannot_confer_verification(self):
        """RegisterView is AllowAny, so an unverified manager stays
        authenticated through it. If the actor check looked only at the role
        they could mint a verified MANAGER and walk around the whole flow."""
        pending = User.objects.create_user(
            username='sec_pending_mgr', email='pending@example.com',
            password='pass1234', role=User.Role.MANAGER)
        self.client.force_authenticate(user=pending)

        self.client.post('/api/auth/register/', {
            'username': 'minted', 'email': 'minted@example.com',
            'first_name': 'M', 'last_name': 'I',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'MANAGER',
        }, format='json')

        self.assertFalse(User.objects.get(username='minted').is_verified)

    def test_a_verified_manager_creating_an_account_confers_verification(self):
        self.client.force_authenticate(user=self.manager)

        self.client.post('/api/auth/register/', {
            'username': 'newslm', 'email': 'newslm@example.com',
            'first_name': 'N', 'last_name': 'S',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'SALESMAN',
        }, format='json')

        self.assertTrue(User.objects.get(username='newslm').is_verified)

    def test_anonymous_can_still_register_as_customer(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'normal', 'email': 'normal@example.com',
            'first_name': 'N', 'last_name': 'O',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'CUSTOMER',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(username='normal').role, 'CUSTOMER')

    def test_manager_may_create_staff_account(self):
        self.client.force_authenticate(user=self.manager)
        resp = self.client.post('/api/auth/register/', {
            'username': 'newstaff', 'email': 'newstaff@example.com',
            'first_name': 'S', 'last_name': 'T',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'ACCOUNTANT',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(User.objects.get(username='newstaff').role, 'ACCOUNTANT')

    def test_is_verified_is_not_settable_from_the_request_body(self):
        """The approval flag must never be self-asserted at signup."""
        resp = self.client.post('/api/auth/register/', {
            'username': 'selfverify', 'email': 'selfverify@example.com',
            'first_name': 'S', 'last_name': 'V',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'CUSTOMER', 'is_verified': True,
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(User.objects.get(username='selfverify').is_verified)

    # --- F6: anonymous writes to the catalogue -----------------------------
    def test_anonymous_cannot_create_product(self):
        resp = self.client.post('/api/products/products/', {'name': 'Sneaky'}, format='json')
        self.assertIn(resp.status_code, (401, 403))
        self.assertFalse(Product.objects.filter(name='Sneaky').exists())

    # --- F5: permission class failing open ---------------------------------
    def test_customer_cannot_delete_audit_log(self):
        log = AuditLog.objects.create(user=self.manager, action='seed')
        self.client.force_authenticate(user=self.customer)
        resp = self.client.delete(f'/api/audit/audit-logs/{log.pk}/')
        self.assertIn(resp.status_code, (403, 405))
        self.assertTrue(AuditLog.objects.filter(pk=log.pk).exists())

    def test_customer_cannot_patch_payment(self):
        self.client.force_authenticate(user=self.customer)
        resp = self.client.patch('/api/finance/payments/1/', {'amount': '1.00'}, format='json')
        self.assertIn(resp.status_code, (403, 404))

    # --- F8: cross-tenant order access -------------------------------------
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

    # --- F7: guest self-verification ---------------------------------------
    def test_customer_cannot_self_verify_website_profile(self):
        self.client.force_authenticate(user=self.customer)
        resp = self.client.post('/api/website/customers/', {'verified': True}, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.json()['verified'], 'verified must not be settable by the applicant')

    # --- F3: /users/me/ under JWT ------------------------------------------
    def test_users_me_works_with_jwt_bearer(self):
        token = self.client.post('/api/auth/token/', {
            'email': 'sec_cust@example.com', 'password': 'pass1234',
        }, format='json').json()['access']

        fresh = APIClient()
        fresh.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = fresh.get('/api/users/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['email'], 'sec_cust@example.com')

    def test_users_me_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/users/me/').status_code, 401)

    # --- token lifetime / expiry behaviour ---------------------------------
    def test_access_token_lifetime_is_configured_not_inherited(self):
        """Guards the bug where SIMPLE_JWT was empty.

        With no explicit setting, simplejwt defaulted to a 5 minute access
        token; combined with a frontend that had no refresh-on-401 path this
        made every request fail with 401 a few minutes after signing in,
        whatever the user's role. Keep this explicit.
        """
        from django.conf import settings
        lifetime = settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME')
        self.assertIsNotNone(
            lifetime, 'ACCESS_TOKEN_LIFETIME must be set explicitly, not inherited')
        self.assertGreaterEqual(lifetime, timedelta(minutes=10))

    def test_expired_access_token_is_rejected_regardless_of_role(self):
        """An expired token must 401 - the frontend relies on that to refresh."""
        refresh = RefreshToken.for_user(self.manager)
        refresh['role'] = self.manager.role
        access = refresh.access_token
        access.set_exp(lifetime=timedelta(seconds=-10))

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        self.assertEqual(client.get('/api/users/me/').status_code, 401)

    def test_refresh_cookie_issues_a_working_access_token(self):
        """The recovery path the frontend retries with must actually work."""
        client = APIClient()
        login = client.post('/api/auth/token/', {
            'email': 'sec_mgr@example.com', 'password': 'pass1234',
        }, format='json')
        self.assertEqual(login.status_code, 200)

        refreshed = client.post('/api/auth/token/refresh/', {}, format='json')
        self.assertEqual(refreshed.status_code, 200)

        fresh = APIClient()
        fresh.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed.json()['access']}")
        me = fresh.get('/api/users/me/')
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['role'], 'MANAGER')

    # --- F9: case-insensitive email uniqueness -----------------------------
    def test_duplicate_email_differing_only_in_case_is_rejected(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'dupe', 'email': 'SEC_CUST@example.com',
            'first_name': 'D', 'last_name': 'U',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'CUSTOMER',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_a_rotated_refresh_token_cannot_be_reused(self):
        """ROTATE_REFRESH_TOKENS is only a security win with blacklisting.

        Rotation alone hands out a new refresh token but leaves the old one
        valid until its natural expiry, so a stolen token has an unbounded
        life - the opposite of what rotation is for.
        """
        client = APIClient()
        login = client.post('/api/auth/token/', {
            'email': 'sec_mgr@example.com', 'password': 'pass1234',
        }, format='json')
        self.assertEqual(login.status_code, 200)
        # The refresh token is returned as an httpOnly cookie, not in the body.
        original_refresh = login.cookies['refresh'].value

        rotated = client.post('/api/auth/token/refresh/', {}, format='json')
        self.assertEqual(rotated.status_code, 200)
        self.assertNotEqual(rotated.cookies['refresh'].value, original_refresh)

        replayed = APIClient().post(
            '/api/auth/token/refresh/', {'refresh': original_refresh}, format='json')
        self.assertEqual(replayed.status_code, 401)


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


class StaffRoleSetTests(TestCase):
    def test_the_staff_role_set_is_defined_once(self):
        """Two hand-maintained copies of "which roles are privileged" drift,
        and the one that drifts silently is a security hole.

        The canonical set lives in permissions.py, beside the check that uses
        it. serializers.py must not keep a rival list.
        """
        from users import serializers as user_serializers
        from users.permissions import STAFF_ROLES

        self.assertEqual(STAFF_ROLES,
                         {'MANAGER', 'ACCOUNTANT', 'SALESMAN', 'WAREHOUSE_WORKER'})
        self.assertFalse(
            hasattr(user_serializers, 'PRIVILEGED_ROLES'),
            'serializers.py is keeping its own copy of the staff-role set.')


class UserAdministrationTests(TestCase):
    """The manager's surface for granting roles and approving accounts."""

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
        self.assertEqual({row['username'] for row in resp.json()},
                         {'adm_mgr', 'adm_slm'})

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

    def test_an_unverified_manager_cannot_administer_users(self):
        pending = User.objects.create_user(
            username='adm_pending', password='pass', role=User.Role.MANAGER)
        self.client.force_authenticate(user=pending)

        self.assertEqual(self.client.get('/api/users/manage/').status_code, 403)

    def test_unauthenticated_is_401(self):
        self.assertEqual(APIClient().get('/api/users/manage/').status_code, 401)
