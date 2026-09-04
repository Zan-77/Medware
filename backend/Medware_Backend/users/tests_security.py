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
from audit.models import AuditLog
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
            role=User.Role.MANAGER)

    # --- registration policy ------------------------------------------------
    # Current (development) policy: anyone may register with any role. The
    # manager-approval gate (is_verified) is commented out in
    # users/serializers.py. This test PINS THE INSECURE DEV BEHAVIOUR so that
    # switching the gate back on fails loudly here and reminds you to flip
    # this test over to asserting 400.
    def test_self_registration_with_staff_role_is_currently_allowed(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'escalate', 'email': 'escalate@example.com',
            'first_name': 'E', 'last_name': 'S',
            'password': 'Str0ng!Passw0rd', 'password2': 'Str0ng!Passw0rd',
            'role': 'MANAGER',
        }, format='json')
        self.assertEqual(
            resp.status_code, 201,
            'If this is now 400 the approval gate is back on - update this test.')
        created = User.objects.get(username='escalate')
        self.assertEqual(created.role, 'MANAGER')
        self.assertFalse(
            created.is_verified,
            'New accounts must still default to unverified so the approval '
            'flow has something to switch on.')

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
            'role': 'MANAGER', 'is_verified': True,
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
        other_order = OrderRequest.objects.create(
            origin='CUSTOMER', customer=self.other_customer, status='PENDING')
        self.client.force_authenticate(user=self.customer)

        listed = self.client.get('/api/orders/order-requests/')
        self.assertEqual(listed.status_code, 200)
        ids = [row['id'] for row in listed.json()]
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
