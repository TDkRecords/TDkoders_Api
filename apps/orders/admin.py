from django.contrib import admin
from .models import Order, OrderItem, OrderPayment, OrderRefund, OrderStatusHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "business",
        "customer",
        "status",
        "total",
        "order_date",
    ]
    list_filter = ["business", "status", "order_date"]
    search_fields = ["order_number", "customer_name", "customer_email"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "product", "quantity", "unit_price"]
    list_filter = ["order__business", "product"]


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "payment_method", "amount", "status", "payment_date"]
    list_filter = ["payment_method", "status", "order__business"]


@admin.register(OrderRefund)
class OrderRefundAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "refund_number",
        "reason",
        "refund_amount",
        "approved_at",
    ]
    list_filter = ["reason", "order__business"]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "previous_status",
        "new_status",
        "changed_by",
        "created_at",
    ]
    list_filter = ["previous_status", "new_status", "order__business"]
