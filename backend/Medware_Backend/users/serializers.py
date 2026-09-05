from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .permissions import STAFF_ROLES

# APPROVAL MODEL: anyone may register, but only a verified manager may hand out
# a staff role directly, and a staff account holds no privileges until a manager
# sets `is_verified`. Enforced in users/permissions.py, not only in the UI.
#
# STAFF_ROLES lives there too, so there is exactly one definition of which roles
# are privileged - the copy that drifts is the one that becomes a hole.


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

    def validate_role(self, value):
        """A staff role may only be granted directly by a verified manager.

        Everyone else may register, but lands unverified and holds no
        privileges until a manager approves the account.

        The actor must be VERIFIED, not merely hold the manager role.
        RegisterView is AllowAny, so an unverified manager stays authenticated
        through it; checking the role alone would let them mint a MANAGER
        account - which create() self-verifies - and bypass the whole gate.
        """
        if value not in STAFF_ROLES:
            return value
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        if actor is not None and actor.is_authenticated and (
            actor.is_superuser
            or (actor.role == User.Role.MANAGER and actor.is_verified)
        ):
            return value
        raise serializers.ValidationError(
            'You are not allowed to assign this role. Staff accounts must be '
            'created by a manager.'
        )

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

        # Only a verified manager can reach this with a staff role (see
        # validate_role), so a manager-created manager is trusted. Everything
        # else waits for approval.
        validated_data['is_verified'] = (
            validated_data.get('role') == User.Role.MANAGER
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
