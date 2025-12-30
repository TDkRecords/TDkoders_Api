from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)
    recipient_email = serializers.StringRelatedField(source="recipient", read_only=True)

    class Meta:
        model = Notification
        fields = "__all__"


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = ["user"]
