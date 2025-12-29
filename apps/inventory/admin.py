from django.contrib import admin
from .models import (
    Warehouse,
    InventoryItem,
    InventoryMovement,
    StockTransfer,
    StockTransferItem,
    StockAdjustment,
)

# Register your models here.

admin.site.register(Warehouse)
admin.site.register(InventoryItem)
admin.site.register(InventoryMovement)
admin.site.register(StockTransfer)
admin.site.register(StockTransferItem)
admin.site.register(StockAdjustment)
