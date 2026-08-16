from django.contrib import admin
from .models import Voucher, PaymentRecord, CommissionRecord, CustomerBalance

admin.site.register(Voucher)
admin.site.register(PaymentRecord)
admin.site.register(CommissionRecord)
admin.site.register(CustomerBalance)
