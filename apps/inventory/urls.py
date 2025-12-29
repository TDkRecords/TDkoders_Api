from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WarehouseViewSet,
    InventoryItemViewSet,
    InventoryMovementViewSet,
    StockTransferViewSet,
    StockTransferItemViewSet,
    StockAdjustmentViewSet,
)

router = DefaultRouter()
router.register(r"warehouses", WarehouseViewSet)
router.register(r"inventory-items", InventoryItemViewSet)
router.register(r"inventory-movements", InventoryMovementViewSet)
router.register(r"stock-transfers", StockTransferViewSet)
router.register(r"stock-transfer-items", StockTransferItemViewSet)
router.register(r"stock-adjustments", StockAdjustmentViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
