from rest_framework import serializers
from .models import AuditLog, RequestTransition


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class RequestTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestTransition
        fields = '__all__'
