from rest_framework import serializers
from .models import WebsiteCustomerProfile, WebsiteCatalog, WebsiteCatalogItem


class WebsiteCustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteCustomerProfile
        fields = ['id', 'user', 'verified', 'created_at', 'notes']
        # `verified` is a staff decision, not something the applicant asserts,
        # and `user` is taken from the authenticated request in the viewset -
        # otherwise a guest could POST {"user": <someone else>, "verified": true}.
        read_only_fields = ['user', 'verified', 'created_at']


class WebsiteCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteCatalog
        fields = '__all__'


class WebsiteCatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteCatalogItem
        fields = '__all__'
