from django.contrib import admin
from .models import (
    DailySummary,
    ProductAnalytics,
    CustomerAnalytics,
    SalesReport,
    BusinessMetrics,
    CategoryPerformance,
)

# Register your models here.

admin.site.register(DailySummary)
admin.site.register(ProductAnalytics)
admin.site.register(CustomerAnalytics)
admin.site.register(SalesReport)
admin.site.register(BusinessMetrics)
admin.site.register(CategoryPerformance)
