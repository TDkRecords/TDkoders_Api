from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.core.models.base import TimeStampedModel, UUIDModel, SoftDeleteModel
from apps.core.models import Business, User, Customer, Product, ProductVariant
from apps.inventory.models import Warehouse


class Order(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Orden de compra/venta.

    ¿Para qué?
    - Registro de todas las ventas del negocio
    - Puede ser venta en tienda, online, o telefónica
    - Incluye productos, cantidades, precios, descuentos, impuestos
    """

    ORDER_STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("pending", "Pendiente"),
        ("confirmed", "Confirmada"),
        ("processing", "En Proceso"),
        ("ready", "Lista para Entregar"),
        ("completed", "Completada"),
        ("cancelled", "Cancelada"),
        ("refunded", "Reembolsada"),
    ]

    ORDER_TYPE_CHOICES = [
        ("in_store", "Venta en Tienda"),
        ("online", "Venta Online"),
        ("phone", "Venta por Teléfono"),
        ("delivery", "Entrega a Domicilio"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="orders"
    )

    # Número único de orden
    order_number = models.CharField(
        max_length=50, unique=True, help_text="Número único de orden (auto-generado)"
    )

    # Cliente (opcional - puede ser venta sin registro)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Datos del cliente (para ventas sin registro)
    customer_name = models.CharField(
        max_length=200, blank=True, help_text="Nombre del cliente si no está registrado"
    )
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Tipo y estado
    order_type = models.CharField(
        max_length=20, choices=ORDER_TYPE_CHOICES, default="in_store"
    )
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS_CHOICES, default="pending"
    )

    # Bodega de origen
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Bodega desde donde se despacha",
    )

    # Montos
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Subtotal antes de descuentos e impuestos",
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Monto total de descuentos",
    )
    tax_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, help_text="Monto de impuestos"
    )
    shipping_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Costo de envío"
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, help_text="Total final a pagar"
    )

    # Dirección de entrega
    delivery_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_state = models.CharField(max_length=100, blank=True)
    delivery_postal_code = models.CharField(max_length=20, blank=True)

    # Fechas importantes
    order_date = models.DateTimeField(
        auto_now_add=True, help_text="Fecha de creación de la orden"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Usuarios responsables
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_orders"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
        help_text="Empleado asignado para procesar la orden",
    )

    # Notas
    notes = models.TextField(blank=True, help_text="Notas internas sobre la orden")
    customer_notes = models.TextField(
        blank=True, help_text="Notas del cliente (instrucciones especiales)"
    )

    class Meta:
        db_table = "orders"
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"
        ordering = ["-order_date"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["customer", "order_date"]),
            models.Index(fields=["order_number"]),
            models.Index(fields=["order_date"]),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.get_status_display()}"

    def clean(self):
        """Validar antes de guardar"""
        super().clean()

        # Validar que el warehouse pertenezca al business
        if self.warehouse and self.warehouse.business != self.business:
            raise ValidationError(
                {"warehouse": "La bodega debe pertenecer al mismo negocio"}
            )

        # Validar que el customer pertenezca al business
        if self.customer and self.customer.business != self.business:
            raise ValidationError(
                {"customer": "El cliente debe pertenecer al mismo negocio"}
            )

    @transaction.atomic
    def mark_as_confirmed(self, user):
        """Confirmar orden y reservar stock"""
        from django.utils import timezone

        if self.status != "pending":
            raise ValidationError("Solo se pueden confirmar órdenes pendientes")

        # Verificar stock disponible
        for item in self.items.all():
            if item.product.track_inventory:
                if item.product.has_variants:
                    if not item.variant:
                        raise ValidationError(
                            f"El producto {item.product.name} requiere una variante"
                        )
                    if item.variant.stock_quantity < item.quantity:
                        raise ValidationError(
                            f"Stock insuficiente para {item.variant.name}"
                        )
                else:
                    if item.product.stock_quantity < item.quantity:
                        raise ValidationError(
                            f"Stock insuficiente para {item.product.name}"
                        )

        # Reservar stock
        for item in self.items.all():
            if item.product.track_inventory:
                if item.product.has_variants:
                    item.variant.deduct_stock(item.quantity)
                else:
                    item.product.stock_quantity -= item.quantity
                    item.product.save(update_fields=["stock_quantity"])

        # Actualizar estado
        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.save(update_fields=["status", "confirmed_at", "updated_at"])

        # Registrar en historial
        OrderStatusHistory.objects.create(
            order=self,
            previous_status="pending",
            new_status="confirmed",
            changed_by=user,
            notes="Orden confirmada y stock reservado",
        )

    def save(self, *args, **kwargs):
        """Auto-genera order_number"""
        if not self.order_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_order = (
                Order.objects.filter(
                    business=self.business, order_number__startswith=f"ORD-{date_str}"
                )
                .order_by("-order_number")
                .first()
            )

            if last_order:
                try:
                    last_num = int(last_order.order_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.order_number = f"ORD-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calcula los totales de la orden basado en los items"""
        items = self.items.all()

        self.subtotal = sum(item.subtotal for item in items)
        self.discount_amount = sum(item.discount_amount for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)

        # Total = Subtotal - Descuentos + Impuestos + Envío
        self.total = (
            self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost
        )

        self.save(
            update_fields=[
                "subtotal",
                "discount_amount",
                "tax_amount",
                "total",
                "updated_at",
            ]
        )

    @property
    def item_count(self):
        """Total de items en la orden"""
        return self.items.count()

    @property
    def total_quantity(self):
        """Cantidad total de productos"""
        return sum(item.quantity for item in self.items.all())


class OrderItem(TimeStampedModel, UUIDModel):
    """
    Item individual de una orden.

    ¿Para qué?
    - Detalla cada producto en la orden
    - Cantidad, precio, descuentos específicos por item
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_items",
    )

    # Cantidad
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)], help_text="Cantidad ordenada"
    )

    # Precios (se guardan por si cambian después)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio unitario al momento de la venta",
    )

    # Descuentos
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Porcentaje de descuento aplicado",
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Monto de descuento en dinero",
    )

    # Impuestos
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tasa de impuesto aplicada",
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Monto de impuesto"
    )

    # Totales
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Subtotal del item (precio × cantidad)",
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total del item después de descuentos e impuestos",
    )

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "order_items"
        verbose_name = "Item de Orden"
        verbose_name_plural = "Items de Orden"
        ordering = ["created_at"]

    def __str__(self):
        variant_name = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_name} (x{self.quantity})"

    def clean(self):
        """Validar antes de guardar"""
        super().clean()

        # Si el producto tiene variantes, debe especificarse una
        if self.product.has_variants and not self.variant:
            raise ValidationError(
                {"variant": "Este producto requiere seleccionar una variante"}
            )

        # Si se especifica variante, debe pertenecer al producto
        if self.variant and self.variant.product != self.product:
            raise ValidationError(
                {"variant": "La variante no pertenece al producto seleccionado"}
            )

    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.clean()
        # Calcula totales automáticamente
        # Subtotal = precio × cantidad
        self.subtotal = self.unit_price * self.quantity

        # Aplicar descuento
        if self.discount_percentage > 0:
            self.discount_amount = self.subtotal * (self.discount_percentage / 100)

        # Calcular base imponible
        base_for_tax = self.subtotal - self.discount_amount

        # Aplicar impuesto
        if self.tax_rate > 0:
            self.tax_amount = base_for_tax * (self.tax_rate / 100)

        # Total = Subtotal - Descuento + Impuesto
        self.total = base_for_tax + self.tax_amount

        super().save(*args, **kwargs)
        # Recalcular totales de la orden
        if self.order_id:
            self.order.calculate_totals()


class OrderStatusHistory(TimeStampedModel, UUIDModel):
    """
    Historial de cambios de estado de la orden.

    ¿Para qué?
    - Trazabilidad completa de la orden
    - Saber quién y cuándo cambió el estado
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_history"
    )

    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)

    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "order_status_history"
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"


class OrderPayment(TimeStampedModel, UUIDModel):
    """
    Pagos asociados a una orden.

    ¿Para qué?
    - Una orden puede tener múltiples pagos (abonos, depósitos)
    - Diferentes métodos de pago (efectivo, tarjeta, transferencia)
    """

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Efectivo"),
        ("card", "Tarjeta"),
        ("transfer", "Transferencia"),
        ("online", "Pago Online"),
        ("other", "Otro"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("completed", "Completado"),
        ("failed", "Fallido"),
        ("refunded", "Reembolsado"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")

    # Número de transacción
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID de transacción externa (Stripe, PayPal, etc)",
    )

    # Método y estado
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )

    # Monto
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # Fechas
    payment_date = models.DateTimeField(auto_now_add=True, help_text="Fecha del pago")

    # Responsable
    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="processed_payments"
    )

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "order_payments"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.order.order_number} - {self.get_payment_method_display()} - ${self.amount}"


class OrderRefund(TimeStampedModel, UUIDModel):
    """
    Devoluciones/reembolsos de órdenes.

    ¿Para qué?
    - Registrar devoluciones totales o parciales
    - Motivo de la devolución
    - Items devueltos
    """

    REFUND_REASON_CHOICES = [
        ("customer_request", "Solicitud del Cliente"),
        ("defective", "Producto Defectuoso"),
        ("wrong_item", "Item Incorrecto"),
        ("not_satisfied", "Cliente Insatisfecho"),
        ("other", "Otro"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refunds")

    # Número de reembolso
    refund_number = models.CharField(max_length=50, unique=True)

    # Razón
    reason = models.CharField(max_length=30, choices=REFUND_REASON_CHOICES)

    # Monto
    refund_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # Responsables
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="requested_refunds"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_refunds",
    )

    # Fechas
    approved_at = models.DateTimeField(null=True, blank=True)

    # Notas
    notes = models.TextField()

    class Meta:
        db_table = "order_refunds"
        verbose_name = "Reembolso"
        verbose_name_plural = "Reembolsos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.refund_number} - {self.order.order_number}"

    def save(self, *args, **kwargs):
        """Auto-genera refund_number"""
        if not self.refund_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_refund = (
                OrderRefund.objects.filter(refund_number__startswith=f"REF-{date_str}")
                .order_by("-refund_number")
                .first()
            )

            if last_refund:
                try:
                    last_num = int(last_refund.refund_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.refund_number = f"REF-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)
