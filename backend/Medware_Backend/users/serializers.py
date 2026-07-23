from rest_framework import serializers

from .models import User


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


class UserManagementSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'role_display',
            'is_active',
            'is_staff',
            'is_superuser',
            'requires_relogin',
            'date_joined',
        ]
        read_only_fields = ['id', 'username', 'email', 'is_superuser', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role', User.Role.CUSTOMER)
        user = User.objects.create_user(
            password=password,
            role=role,
            **validated_data,
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
