from django.contrib import admin
from .models import WebsiteCustomerProfile, WebsiteCatalog, WebsiteCatalogItem

admin.site.register(WebsiteCustomerProfile)
admin.site.register(WebsiteCatalog)
admin.site.register(WebsiteCatalogItem)
