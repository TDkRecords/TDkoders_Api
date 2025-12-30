from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "business",
        "notification_type",
        "priority",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "priority", "is_read", "business")
    search_fields = ("title", "message", "recipient__email")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "business",
        "allow_in_app",
        "allow_email",
        "allow_sms",
        "allow_push",
        "is_muted",
    )
    list_filter = ("business", "is_muted")
    search_fields = ("user__email",)
