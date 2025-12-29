from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, OrderPayment, OrderRefund


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = "__all__"


class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPayment
        fields = "__all__"


class OrderRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderRefund
        fields = "__all__"


# Serializers for nested relationships (optional but useful for complex views)
class OrderItemWithProductSerializer(OrderItemSerializer):
    product = serializers.StringRelatedField()


class OrderWithItemsSerializer(OrderSerializer):
    items = OrderItemWithProductSerializer(many=True, read_only=True)


# Serializer for creating orders (write-only)
class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "business",
            "customer",
            "order_type",
            "warehouse",
            "payment_method",
            "notes",
            "discount_amount",
            "tax_amount",
        ]

    def create(self, validated_data):
        # Custom creation logic can be added here if needed
        return Order.objects.create(**validated_data)


class OrderDetailSerializer(OrderWithItemsSerializer):
    payments = OrderPaymentSerializer(many=True, read_only=True)
    refunds = OrderRefundSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
