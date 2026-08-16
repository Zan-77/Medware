from rest_framework import serializers
from .models import WebsiteCustomerProfile, WebsiteCatalog, WebsiteCatalogItem


class WebsiteCustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteCustomerProfile
        fields = '__all__'


class WebsiteCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteCatalog
        fields = '__all__'


class WebsiteCatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteCatalogItem
        fields = '__all__'
