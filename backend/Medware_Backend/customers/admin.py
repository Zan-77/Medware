from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'status', 'created_by', 'user')
    list_filter = ('status',)
    search_fields = ('name', 'phone')
