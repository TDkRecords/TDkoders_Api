from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r"daily-summary", views.DailySummaryViewSet, basename="daily-summary")
router.register(
    r"product-analytics", views.ProductAnalyticsViewSet, basename="product-analytics"
)
router.register(
    r"customer-analytics", views.CustomerAnalyticsViewSet, basename="customer-analytics"
)
router.register(r"sales-reports", views.SalesReportViewSet, basename="sales-reports")
router.register(
    r"business-metrics", views.BusinessMetricsViewSet, basename="business-metrics"
)
router.register(
    r"category-performance",
    views.CategoryPerformanceViewSet,
    basename="category-performance",
)

urlpatterns = [
    path("", include(router.urls)),
]
