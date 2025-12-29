from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models.base import TimeStampedModel, UUIDModel, SoftDeleteModel
from apps.core.models import Business, Product, ProductVariant, User


class Warehouse(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Bodega o almacén del negocio.

    ¿Para qué?
    - Un negocio puede tener MÚLTIPLES ubicaciones de almacenamiento
    - Ejemplo: Bodega principal, Bodega secundaria, Tienda 1, Tienda 2
    - Cada ubicación tiene su propio stock
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="warehouses"
    )

    # Información básica
    name = models.CharField(
        max_length=100,
        help_text="Nombre de la bodega (ej: Bodega Principal, Tienda Centro)",
    )
    code = models.CharField(
        max_length=20, help_text="Código único de la bodega (ej: BOD-01, TDA-CENTRO)"
    )

    # Ubicación
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Contacto
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_warehouses",
        help_text="Encargado de la bodega",
    )

    # Configuración
    is_main = models.BooleanField(default=False, help_text="¿Es la bodega principal?")
    is_active = models.BooleanField(default=True)

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "warehouses"
        verbose_name = "Bodega"
        verbose_name_plural = "Bodegas"
        unique_together = [["business", "code"]]
        ordering = ["-is_main", "name"]
        indexes = [
            models.Index(fields=["business", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class InventoryItem(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Registro de inventario por variante y bodega.

    ¿Para qué?
    - Controla el stock de cada variante en cada bodega
    - Ejemplo: "Camisa Azul M" tiene 10 unidades en "Bodega Principal"
    - Permite saber exactamente dónde está cada producto

    IMPORTANTE: Este modelo reemplaza el campo stock_quantity de ProductVariant
    cuando se usan múltiples bodegas.
    """

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="inventory_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="inventory_items"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="inventory_items",
        help_text="Si el producto tiene variantes, especificar cuál",
    )

    # Stock
    quantity = models.IntegerField(
        default=0, help_text="Cantidad disponible en esta bodega"
    )
    reserved_quantity = models.IntegerField(
        default=0, help_text="Cantidad reservada (en órdenes pendientes)"
    )

    # Ubicación dentro de la bodega
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ubicación física dentro de la bodega (ej: Pasillo 3, Estante A)",
    )

    # Alertas
    min_stock_level = models.IntegerField(
        default=0, help_text="Nivel mínimo antes de alertar"
    )
    max_stock_level = models.IntegerField(
        default=0, help_text="Nivel máximo recomendado"
    )

    # Costos
    average_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Costo promedio ponderado",
    )

    class Meta:
        db_table = "inventory_items"
        verbose_name = "Item de Inventario"
        verbose_name_plural = "Items de Inventario"
        unique_together = [["warehouse", "product", "variant"]]
        ordering = ["warehouse", "product"]
        indexes = [
            models.Index(fields=["warehouse", "product"]),
            models.Index(fields=["quantity"]),
        ]

    def __str__(self):
        variant_name = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_name} @ {self.warehouse.name}"

    @property
    def available_quantity(self):
        """Cantidad disponible (total - reservado)"""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def is_low_stock(self):
        """¿Está por debajo del nivel mínimo?"""
        return self.quantity <= self.min_stock_level

    @property
    def is_overstock(self):
        """¿Está por encima del nivel máximo?"""
        if self.max_stock_level > 0:
            return self.quantity >= self.max_stock_level
        return False

    def reserve(self, quantity):
        """Reserva cantidad para una orden"""
        if self.available_quantity >= quantity:
            self.reserved_quantity += quantity
            self.save(update_fields=["reserved_quantity", "updated_at"])
            return True
        return False

    def release_reservation(self, quantity):
        """Libera cantidad reservada"""
        self.reserved_quantity = max(0, self.reserved_quantity - quantity)
        self.save(update_fields=["reserved_quantity", "updated_at"])


class InventoryMovement(TimeStampedModel, UUIDModel):
    """
    Registro de todos los movimientos de inventario.

    ¿Para qué?
    - Trazabilidad completa de stock
    - Saber quién, cuándo y por qué cambió el inventario
    - Auditoría y reportes

    Tipos de movimientos:
    - purchase: Compra a proveedor
    - sale: Venta a cliente
    - transfer: Transferencia entre bodegas
    - adjustment: Ajuste manual
    - return: Devolución
    - damage: Producto dañado
    """

    MOVEMENT_TYPE_CHOICES = [
        ("purchase", "Compra"),
        ("sale", "Venta"),
        ("transfer", "Transferencia"),
        ("adjustment", "Ajuste"),
        ("return", "Devolución"),
        ("damage", "Daño/Pérdida"),
        ("production", "Producción"),
        ("consumption", "Consumo"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="inventory_movements"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="movements"
    )

    # Tipo de movimiento
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)

    # Cantidad
    quantity = models.IntegerField(
        help_text="Cantidad movida (positivo = entrada, negativo = salida)"
    )

    # Stock antes y después
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()

    # Referencia
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tipo de documento (Order, PurchaseOrder, Transfer, etc)",
    )
    reference_id = models.CharField(
        max_length=100, blank=True, help_text="ID del documento relacionado"
    )

    # Costos
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo unitario en este movimiento",
    )
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo total del movimiento",
    )

    # Usuario responsable
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_movements",
    )

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "inventory_movements"
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "movement_type"]),
            models.Index(fields=["inventory_item", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.inventory_item} ({self.quantity})"

    def save(self, *args, **kwargs):
        """Calcula total_cost si no está definido"""
        if self.unit_cost and not self.total_cost:
            self.total_cost = abs(self.quantity) * self.unit_cost
        super().save(*args, **kwargs)


class StockTransfer(TimeStampedModel, UUIDModel):
    """
    Transferencia de stock entre bodegas.

    ¿Para qué?
    - Mover productos entre ubicaciones
    - Ejemplo: Transferir 50 unidades de Bodega Principal a Tienda Centro
    - Control de traslados en tránsito
    """

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("in_transit", "En Proceso de Transferencia"),
        ("completed", "Completado"),
        ("cancelled", "Cancelado"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="stock_transfers"
    )

    # Bodegas
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="outgoing_transfers"
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="incoming_transfers"
    )

    # Número de transferencia
    transfer_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número único de transferencia (auto-generado)",
    )

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Fechas
    transfer_date = models.DateTimeField(
        help_text="Fecha de inicio de la transferencia"
    )
    expected_arrival = models.DateTimeField(
        null=True, blank=True, help_text="Fecha esperada de llegada"
    )
    completed_date = models.DateTimeField(
        null=True, blank=True, help_text="Fecha de completación"
    )

    # Responsables
    initiated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="initiated_transfers"
    )
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_transfers",
    )

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "stock_transfers"
        verbose_name = "Transferencia de Stock"
        verbose_name_plural = "Transferencias de Stock"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["from_warehouse", "to_warehouse"]),
        ]

    def __str__(self):
        return f"{self.transfer_number}: {self.from_warehouse} → {self.to_warehouse}"

    def save(self, *args, **kwargs):
        """Auto-genera transfer_number"""
        if not self.transfer_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_transfer = (
                StockTransfer.objects.filter(
                    business=self.business,
                    transfer_number__startswith=f"TRF-{date_str}",
                )
                .order_by("-transfer_number")
                .first()
            )

            if last_transfer:
                try:
                    last_num = int(last_transfer.transfer_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.transfer_number = f"TRF-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)


class StockTransferItem(TimeStampedModel, UUIDModel):
    """
    Items de una transferencia de stock.

    ¿Para qué?
    - Detalla qué productos y cantidades se transfieren
    - Una transferencia puede tener múltiples items
    """

    transfer = models.ForeignKey(
        StockTransfer, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, null=True, blank=True
    )

    # Cantidades
    quantity_sent = models.IntegerField(
        validators=[MinValueValidator(1)], help_text="Cantidad enviada"
    )
    quantity_received = models.IntegerField(
        default=0, help_text="Cantidad recibida (puede diferir de la enviada)"
    )

    # Notas
    notes = models.TextField(
        blank=True, help_text="Notas sobre discrepancias, daños, etc."
    )

    class Meta:
        db_table = "stock_transfer_items"
        verbose_name = "Item de Transferencia"
        verbose_name_plural = "Items de Transferencia"
        ordering = ["product"]

    def __str__(self):
        variant_name = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_name} ({self.quantity_sent} unidades)"


class StockAdjustment(TimeStampedModel, UUIDModel):
    """
    Ajustes manuales de inventario.

    ¿Para qué?
    - Corregir discrepancias en inventario
    - Ejemplo: Conteo físico difiere del sistema
    - Registrar pérdidas, daños, robos
    - Ajustes por vencimiento
    """

    REASON_CHOICES = [
        ("count_discrepancy", "Discrepancia en Conteo"),
        ("damage", "Producto Dañado"),
        ("theft", "Robo"),
        ("expired", "Vencido"),
        ("found", "Producto Encontrado"),
        ("correction", "Corrección de Error"),
        ("other", "Otro"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="stock_adjustments"
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="adjustments"
    )

    # Número de ajuste
    adjustment_number = models.CharField(max_length=50, unique=True)

    # Razón
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)

    # Cantidades
    previous_quantity = models.IntegerField()
    adjustment_quantity = models.IntegerField(
        help_text="Cantidad ajustada (positivo = aumenta, negativo = disminuye)"
    )
    new_quantity = models.IntegerField()

    # Responsable y aprobación
    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="performed_adjustments"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_adjustments",
    )

    # Notas
    notes = models.TextField()

    class Meta:
        db_table = "stock_adjustments"
        verbose_name = "Ajuste de Stock"
        verbose_name_plural = "Ajustes de Stock"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "reason"]),
            models.Index(fields=["inventory_item", "created_at"]),
        ]

    def __str__(self):
        return f"{self.adjustment_number}: {self.inventory_item} ({self.adjustment_quantity:+d})"

    def save(self, *args, **kwargs):
        """Auto-genera adjustment_number"""
        if not self.adjustment_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_adjustment = (
                StockAdjustment.objects.filter(
                    business=self.business,
                    adjustment_number__startswith=f"ADJ-{date_str}",
                )
                .order_by("-adjustment_number")
                .first()
            )

            if last_adjustment:
                try:
                    last_num = int(last_adjustment.adjustment_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.adjustment_number = f"ADJ-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)
