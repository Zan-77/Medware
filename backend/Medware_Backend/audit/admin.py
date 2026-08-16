from django.contrib import admin
from .models import AuditLog, RequestTransition

admin.site.register(AuditLog)
admin.site.register(RequestTransition)
