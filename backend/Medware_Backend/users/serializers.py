from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


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

        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = attrs.get('refresh')
        request = self.context.get('request')
        if not refresh and request is not None:
            refresh = request.COOKIES.get('refresh')

        if not refresh:
            raise serializers.ValidationError({'detail': 'Refresh token cookie missing.'})

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
            'password',
            'password2',
            'role',
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
        return User.objects.create_user(**validated_data, password=password)


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'role_display',
            'is_staff',
            'is_superuser',
        ]
