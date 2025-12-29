from rest_framework import viewsets
from apps.inventory.models import (
    Warehouse,
    InventoryItem,
    InventoryMovement,
    StockTransfer,
    StockTransferItem,
    StockAdjustment,
)
from apps.inventory.serializers import (
    WarehouseSerializer,
    InventoryItemSerializer,
    InventoryMovementSerializer,
    StockTransferSerializer,
    StockTransferItemSerializer,
    StockAdjustmentSerializer,
)

# Create your views here.


class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    queryset = Warehouse.objects.all()


class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    queryset = InventoryItem.objects.all()


class InventoryMovementViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryMovementSerializer
    queryset = InventoryMovement.objects.all()


class StockTransferViewSet(viewsets.ModelViewSet):
    serializer_class = StockTransferSerializer
    queryset = StockTransfer.objects.all()


class StockTransferItemViewSet(viewsets.ModelViewSet):
    serializer_class = StockTransferItemSerializer
    queryset = StockTransferItem.objects.all()


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    serializer_class = StockAdjustmentSerializer
    queryset = StockAdjustment.objects.all()
