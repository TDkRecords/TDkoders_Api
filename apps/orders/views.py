from rest_framework import viewsets, permissions
from django.db.models import Prefetch

from .models import (
    Order,
    OrderItem,
    OrderStatusHistory,
    OrderPayment,
    OrderRefund,
)

from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderWithItemsSerializer,
    OrderItemSerializer,
    OrderStatusHistorySerializer,
    OrderPaymentSerializer,
    OrderRefundSerializer,
    OrderItemWithProductSerializer,
    OrderDetailSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(is_deleted=False)

        if self.action == "list":
            return queryset.select_related(
                "business",
                "customer",
                "warehouse",
            ).prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product", "variant"),
                )
            )

        if self.action == "retrieve":
            return queryset.select_related(
                "business",
                "customer",
                "warehouse",
            ).prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related("product", "variant"),
                ),
                "payments",
                "refunds",
                "status_history",
            )

        return queryset

    def get_serializer_class(self):
        return {
            "create": OrderCreateSerializer,
            "list": OrderWithItemsSerializer,
            "retrieve": OrderDetailSerializer,
        }.get(self.action, OrderSerializer)

    def perform_create(self, serializer):
        order = serializer.save(created_by=self.request.user)
        order.calculate_totals()


class OrderItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.select_related("product", "variant")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return OrderItemWithProductSerializer
        return OrderItemSerializer

    def perform_create(self, serializer):
        item = serializer.save()
        item.order.calculate_totals()
