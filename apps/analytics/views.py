from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import (
    DailySummary,
    ProductAnalytics,
    CustomerAnalytics,
    SalesReport,
    BusinessMetrics,
    CategoryPerformance,
)

from .serializers import (
    DailySummarySerializer,
    ProductAnalyticsSerializer,
    CustomerAnalyticsSerializer,
    SalesReportSerializer,
    BusinessMetricsSerializer,
    CategoryPerformanceSerializer,
)


# Base común para todas las analíticas
class BusinessAnalyticsBaseViewSet(ReadOnlyModelViewSet):
    """
    ViewSet base para métricas y analíticas del negocio.
    Incluye filtros comunes por business y fechas.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtro por negocio
        business_id = self.request.query_params.get("business")
        if business_id:
            queryset = queryset.filter(business_id=business_id)

        # Filtro por período
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date and end_date:
            queryset = queryset.filter(
                period_start__gte=start_date,
                period_end__lte=end_date,
            )

        return queryset


# Daily Summary
class DailySummaryViewSet(BusinessAnalyticsBaseViewSet):
    queryset = DailySummary.objects.select_related("business")
    serializer_class = DailySummarySerializer

    def get_queryset(self):
        qs = super().get_queryset()

        date = self.request.query_params.get("date")
        if date:
            qs = qs.filter(date=date)

        return qs


# Product Analytics
class ProductAnalyticsViewSet(BusinessAnalyticsBaseViewSet):
    queryset = ProductAnalytics.objects.select_related(
        "business",
        "product",
        "variant",
    )
    serializer_class = ProductAnalyticsSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        product_id = self.request.query_params.get("product")
        period_type = self.request.query_params.get("period_type")

        if product_id:
            qs = qs.filter(product_id=product_id)

        if period_type:
            qs = qs.filter(period_type=period_type)

        return qs


# Customer Analytics
class CustomerAnalyticsViewSet(BusinessAnalyticsBaseViewSet):
    queryset = CustomerAnalytics.objects.select_related(
        "business",
        "customer",
        "customer__user",
    )
    serializer_class = CustomerAnalyticsSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        rfm_segment = self.request.query_params.get("rfm_segment")
        if rfm_segment:
            qs = qs.filter(rfm_segment=rfm_segment)

        return qs


# Sales Reports
class SalesReportViewSet(BusinessAnalyticsBaseViewSet):
    queryset = SalesReport.objects.select_related(
        "business",
        "generated_by",
    )
    serializer_class = SalesReportSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        report_type = self.request.query_params.get("report_type")
        if report_type:
            qs = qs.filter(report_type=report_type)

        return qs


# Business Metrics (KPIs)
class BusinessMetricsViewSet(BusinessAnalyticsBaseViewSet):
    queryset = BusinessMetrics.objects.select_related("business")
    serializer_class = BusinessMetricsSerializer


# Category Performance
class CategoryPerformanceViewSet(BusinessAnalyticsBaseViewSet):
    queryset = CategoryPerformance.objects.select_related(
        "business",
        "category",
    )
    serializer_class = CategoryPerformanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs
