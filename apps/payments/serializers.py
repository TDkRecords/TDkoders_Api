from rest_framework import serializers
from .models import Payment, PaymentWebhookEvent


class PaymentSerializer(serializers.ModelSerializer):
    business_name = serializers.StringRelatedField(source="business", read_only=True)
    invoice_number = serializers.StringRelatedField(source="invoice", read_only=True)
    order_number = serializers.StringRelatedField(source="order", read_only=True)
    created_by_email = serializers.StringRelatedField(
        source="created_by", read_only=True
    )

    class Meta:
        model = Payment
        fields = "__all__"


class PaymentWebhookEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentWebhookEvent
        fields = "__all__"
