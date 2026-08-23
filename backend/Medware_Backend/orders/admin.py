from django.contrib import admin
from .models import OrderRequest, OrderItem, OrderReview, OrderFinalization, PackagingTask, ReturnRequest, ReturnAssessment, ReturnApproval

admin.site.register(OrderRequest)
admin.site.register(OrderItem)
admin.site.register(OrderReview)
admin.site.register(OrderFinalization)
admin.site.register(PackagingTask)
admin.site.register(ReturnRequest)
admin.site.register(ReturnAssessment)
admin.site.register(ReturnApproval)
