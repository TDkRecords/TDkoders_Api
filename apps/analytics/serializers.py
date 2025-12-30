from rest_framework import serializers

from .models import (
    DailySummary,
    ProductAnalytics,
    CustomerAnalytics,
    SalesReport,
    BusinessMetrics,
    CategoryPerformance,
)


class DailySummarySerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)

    class Meta:
        model = DailySummary
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ProductAnalyticsSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)
    product_name = serializers.StringRelatedField(source="product", read_only=True)
    variant_name = serializers.StringRelatedField(source="variant", read_only=True)

    class Meta:
        model = ProductAnalytics
        fields = "__all__"
        read_only_fields = [
            "id",
            "gross_profit",
            "profit_margin",
            "average_price",
            "created_at",
            "updated_at",
        ]


class CustomerAnalyticsSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)
    customer_name = serializers.CharField(
        source="customer.user.full_name", read_only=True
    )

    class Meta:
        model = CustomerAnalytics
        fields = "__all__"
        read_only_fields = [
            "id",
            "average_order_value",
            "purchase_frequency",
            "days_since_last_purchase",
            "rfm_segment",
            "lifetime_value",
            "predicted_lifetime_value",
            "created_at",
            "updated_at",
        ]


class SalesReportSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)
    generated_by_name = serializers.StringRelatedField(
        source="generated_by", read_only=True
    )
    report_type_display = serializers.CharField(
        source="get_report_type_display", read_only=True
    )

    class Meta:
        model = SalesReport
        fields = "__all__"
        read_only_fields = [
            "id",
            "sales_growth",
            "top_products",
            "top_customers",
            "detailed_data",
            "generated_by",
            "created_at",
            "updated_at",
        ]


class BusinessMetricsSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)

    class Meta:
        model = BusinessMetrics
        fields = "__all__"
        read_only_fields = [
            "id",
            "revenue_growth",
            "gross_profit_margin",
            "net_profit_margin",
            "customer_retention_rate",
            "customer_churn_rate",
            "inventory_turnover",
            "days_inventory_outstanding",
            "cost_per_acquisition",
            "created_at",
            "updated_at",
        ]


class CategoryPerformanceSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)
    category_name = serializers.StringRelatedField(source="category", read_only=True)

    class Meta:
        model = CategoryPerformance
        fields = "__all__"
        read_only_fields = [
            "id",
            "sales_percentage",
            "profit_margin",
            "sales_growth",
            "created_at",
            "updated_at",
        ]
