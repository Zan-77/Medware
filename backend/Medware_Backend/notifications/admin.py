from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('kind', 'recipient', 'target_type', 'target_id', 'created_at', 'read_at')
    list_filter = ('kind',)
