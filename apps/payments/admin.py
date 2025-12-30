from django.contrib import admin
from .models import Payment, PaymentWebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "payment_number",
        "business",
        "amount",
        "status",
        "provider",
        "created_at",
    ]
    list_filter = ["status", "provider", "created_at"]
    search_fields = ["payment_number", "invoice__number", "order__number"]


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ["external_id", "business", "provider", "event_type", "created_at"]
    list_filter = ["provider", "event_type", "created_at"]
    search_fields = ["external_id", "event_type"]


# Register your models here.
