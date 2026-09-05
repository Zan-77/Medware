from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

# APPROVAL MODEL: anyone may register, but only a verified manager may hand out
# a staff role directly, and a staff account holds no privileges until a manager
# sets `is_verified`. Enforced in users/permissions.py, not only in the UI.
#
# STAFF_ROLES lives in users/permissions.py - one definition of which roles are
# privileged, next to the check that uses it.


def build_tokens_for_user(user):
    """Issue a refresh/access pair carrying the claims the frontend reads.

    Single definition so the register and login paths can never drift apart.
    """
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role
    refresh['first_name'] = user.first_name
    refresh['last_name'] = user.last_name
    refresh['email'] = user.email
    # The frontend decodes this for its first render. It is a snapshot: the
    # access token lives 15 minutes, so after a manager approves an account
    # this claim lags. /api/users/me/ is the authoritative source.
    refresh['is_verified'] = user.is_verified
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class EmailOrUsernameTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        email = attrs.get('email')
        username = attrs.get('username')
        identifier = email or username

        if not identifier:
            raise serializers.ValidationError({'detail': 'Email or username is required.'})
        if not password:
            raise serializers.ValidationError({'detail': 'Password is required.'})

        user = None
        if email:
            user = User.objects.filter(email__iexact=email).first()
        if user is None and username:
            user = User.objects.filter(username__iexact=username).first()

        if user is None or not user.check_password(password):
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        if not user.is_active:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})

        return build_tokens_for_user(user)


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    # The parent declares `refresh` as required, so with no cookie present
    # field validation failed before validate() ever ran - the "cookie
    # missing" branch below was unreachable and callers got a confusing
    # 400 {"refresh": ["This field is required."]}. Making it optional here
    # lets validate() own the missing-token case and answer 401, which is
    # what "your session has expired / you are not signed in" should be.
    refresh = serializers.CharField(required=False)

    def validate(self, attrs):
        refresh = attrs.get('refresh')
        request = self.context.get('request')
        if not refresh and request is not None:
            refresh = request.COOKIES.get('refresh')

        if not refresh:
            raise AuthenticationFailed('No refresh token cookie; not signed in.')

        attrs['refresh'] = refresh
        return super().validate(attrs)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password2',
            'role',
            'is_verified',
        ]

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': "Password fields didn't match."})

        email = data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'A user with that email already exists.'})

        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        validated_data.setdefault('role', User.Role.CUSTOMER)

        # Anyone may REQUEST any role - registration never fails on the role,
        # so the frontend can show "awaiting approval" instead of an error.
        # What is gated is whether the account is verified, and a role does
        # nothing at all until it is (users/permissions.py).
        #
        # Verification is conferred by the ACTOR, never by the requested role.
        # Deriving it from the role instead would mean anyone self-registering
        # as MANAGER was born verified - the entire gate, bypassed by a
        # dropdown. And the actor must itself be verified: RegisterView is
        # AllowAny, so an unverified manager stays authenticated through it.
        actor = getattr(self.context.get('request'), 'user', None)
        validated_data['is_verified'] = bool(
            actor is not None
            and actor.is_authenticated
            and (
                actor.is_superuser
                or (actor.role == User.Role.MANAGER and actor.is_verified)
            )
        )

        return User.objects.create_user(**validated_data, password=password)


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'is_staff',
            'is_superuser',
            'is_verified',
        ]


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
