from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models.base import TimeStampedModel, UUIDModel, SoftDeleteModel
from apps.core.models import Business, User, Customer, Product
from apps.orders.models import Order
from apps.inventory.models import Warehouse


class Account(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Cuentas contables del negocio.

    ¿Para qué?
    - Organizar las finanzas en categorías (Ventas, Gastos, Activos, etc.)
    - Similar a un plan de cuentas contable simplificado
    """

    ACCOUNT_TYPE_CHOICES = [
        ("asset", "Activo"),  # Lo que posees (efectivo, inventario)
        ("liability", "Pasivo"),  # Lo que debes (préstamos, cuentas por pagar)
        ("equity", "Capital"),  # Patrimonio del negocio
        ("revenue", "Ingreso"),  # Ventas y otros ingresos
        ("expense", "Gasto"),  # Costos operativos
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="accounts"
    )

    # Información básica
    code = models.CharField(
        max_length=20, help_text="Código de cuenta (ej: 1001, 4001)"
    )
    name = models.CharField(
        max_length=200, help_text="Nombre de la cuenta (ej: Caja, Ventas)"
    )
    description = models.TextField(blank=True)

    # Tipo
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)

    # Jerarquía (cuenta padre para subcuentas)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_accounts",
    )

    # Balance
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Balance actual de la cuenta",
    )

    # Estado
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounts"
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        unique_together = [["business", "code"]]
        ordering = ["code", "name"]
        indexes = [
            models.Index(fields=["business", "account_type"]),
            models.Index(fields=["business", "is_active"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Transacciones financieras.

    ¿Para qué?
    - Registrar todos los movimientos de dinero
    - Base del sistema de contabilidad por partida doble
    """

    TRANSACTION_TYPE_CHOICES = [
        ("sale", "Venta"),
        ("purchase", "Compra"),
        ("payment", "Pago"),
        ("receipt", "Cobro"),
        ("transfer", "Transferencia"),
        ("adjustment", "Ajuste"),
        ("refund", "Reembolso"),
        ("expense", "Gasto"),
        ("other", "Otro"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="transactions"
    )

    # Número de transacción
    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número único de transacción (auto-generado)",
    )

    # Tipo y fecha
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    transaction_date = models.DateTimeField(help_text="Fecha de la transacción")

    # Referencia a otros modelos
    reference_type = models.CharField(
        max_length=50, blank=True, help_text="Tipo de documento (Order, Invoice, etc)"
    )
    reference_id = models.CharField(
        max_length=100, blank=True, help_text="ID del documento relacionado"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    # Monto total
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # Descripción
    description = models.TextField()
    notes = models.TextField(blank=True)

    # Usuario responsable
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_transactions"
    )

    # Estado
    is_posted = models.BooleanField(
        default=False, help_text="¿La transacción está contabilizada?"
    )
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "transactions"
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ["-transaction_date"]
        indexes = [
            models.Index(fields=["business", "transaction_type"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()}"

    def save(self, *args, **kwargs):
        """Auto-genera transaction_number"""
        if not self.transaction_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_transaction = (
                Transaction.objects.filter(
                    business=self.business,
                    transaction_number__startswith=f"TXN-{date_str}",
                )
                .order_by("-transaction_number")
                .first()
            )

            if last_transaction:
                try:
                    last_num = int(last_transaction.transaction_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.transaction_number = f"TXN-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)


class TransactionEntry(TimeStampedModel, UUIDModel):
    """
    Asientos contables (partida doble).

    ¿Para qué?
    - Cada transacción tiene al menos 2 entradas (débito y crédito)
    - Sistema de contabilidad por partida doble
    - Asegura que los libros siempre estén balanceados
    """

    ENTRY_TYPE_CHOICES = [
        ("debit", "Débito"),  # Suma al balance (activos y gastos)
        ("credit", "Crédito"),  # Resta al balance (pasivos, capital, ingresos)
    ]

    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="entries"
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="entries"
    )

    # Tipo y monto
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # Descripción
    description = models.TextField(blank=True)

    class Meta:
        db_table = "transaction_entries"
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ["transaction", "entry_type"]
        indexes = [
            models.Index(fields=["transaction", "account"]),
        ]

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.account.name}: ${self.amount}"


class Invoice(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Facturas emitidas por el negocio.

    ¿Para qué?
    - Documento formal de venta
    - Cumplimiento fiscal
    - Control de cuentas por cobrar
    """

    STATUS_CHOICES = [
        ("draft", "Borrador"),
        ("sent", "Enviada"),
        ("paid", "Pagada"),
        ("partially_paid", "Parcialmente Pagada"),
        ("overdue", "Vencida"),
        ("cancelled", "Cancelada"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="invoices"
    )

    # Número de factura
    invoice_number = models.CharField(
        max_length=50, unique=True, help_text="Número único de factura (auto-generado)"
    )

    # Cliente
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )

    # Orden relacionada
    order = models.OneToOneField(
        Order, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoice"
    )

    # Fechas
    issue_date = models.DateField(help_text="Fecha de emisión")
    due_date = models.DateField(help_text="Fecha de vencimiento")
    paid_date = models.DateField(null=True, blank=True)

    # Montos
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Notas
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True, help_text="Términos y condiciones")

    class Meta:
        db_table = "invoices"
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-issue_date"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer}"

    def save(self, *args, **kwargs):
        """Auto-genera invoice_number"""
        if not self.invoice_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_invoice = (
                Invoice.objects.filter(
                    business=self.business, invoice_number__startswith=f"INV-{date_str}"
                )
                .order_by("-invoice_number")
                .first()
            )

            if last_invoice:
                try:
                    last_num = int(last_invoice.invoice_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.invoice_number = f"INV-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        """Saldo pendiente"""
        return self.total - self.amount_paid

    @property
    def is_paid(self):
        """¿Está pagada completamente?"""
        return self.amount_paid >= self.total


class Expense(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Gastos del negocio.

    ¿Para qué?
    - Control de todos los gastos operativos
    - Análisis de rentabilidad
    - Reportes financieros
    """

    CATEGORY_CHOICES = [
        ("rent", "Arriendo"),
        ("utilities", "Servicios Públicos"),
        ("salaries", "Salarios"),
        ("supplies", "Suministros"),
        ("marketing", "Marketing"),
        ("maintenance", "Mantenimiento"),
        ("insurance", "Seguros"),
        ("taxes", "Impuestos"),
        ("equipment", "Equipo"),
        ("other", "Otro"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("paid", "Pagado"),
        ("partially_paid", "Parcialmente Pagado"),
        ("overdue", "Vencido"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="expenses"
    )

    # Número de gasto
    expense_number = models.CharField(
        max_length=50, unique=True, help_text="Número único de gasto (auto-generado)"
    )

    # Información básica
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    # Proveedor (opcional)
    vendor_name = models.CharField(
        max_length=200, blank=True, help_text="Nombre del proveedor"
    )

    # Fechas
    expense_date = models.DateField(help_text="Fecha del gasto")
    due_date = models.DateField(
        null=True, blank=True, help_text="Fecha de vencimiento de pago"
    )
    paid_date = models.DateField(null=True, blank=True)

    # Montos
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    # Estado de pago
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    payment_method = models.CharField(
        max_length=50, blank=True, help_text="Método de pago utilizado"
    )

    # Archivo adjunto
    receipt_url = models.URLField(blank=True, help_text="URL del recibo/factura en S3")

    # Usuario responsable
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_expenses"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
    )

    # ¿Es recurrente?
    is_recurring = models.BooleanField(default=False)
    recurring_frequency = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("daily", "Diario"),
            ("weekly", "Semanal"),
            ("monthly", "Mensual"),
            ("yearly", "Anual"),
        ],
    )

    class Meta:
        db_table = "expenses"
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ["-expense_date"]
        indexes = [
            models.Index(fields=["business", "category"]),
            models.Index(fields=["business", "payment_status"]),
            models.Index(fields=["expense_date"]),
        ]

    def __str__(self):
        return f"{self.expense_number} - {self.description}"

    def save(self, *args, **kwargs):
        """Auto-genera expense_number y calcula total"""
        if not self.expense_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_expense = (
                Expense.objects.filter(
                    business=self.business, expense_number__startswith=f"EXP-{date_str}"
                )
                .order_by("-expense_number")
                .first()
            )

            if last_expense:
                try:
                    last_num = int(last_expense.expense_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.expense_number = f"EXP-{date_str}-{new_num:04d}"

        # Calcular total
        self.total = self.amount + self.tax_amount

        super().save(*args, **kwargs)


class PaymentTerm(TimeStampedModel, UUIDModel):
    """
    Términos de pago predefinidos.

    ¿Para qué?
    - Definir plazos de pago estándar
    - Ejemplo: "Net 30" (pago a 30 días)
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="payment_terms"
    )

    name = models.CharField(
        max_length=100, help_text="Nombre del término (ej: Net 30, 50% Adelanto)"
    )
    days = models.IntegerField(help_text="Días de plazo para pago")
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Descuento por pronto pago",
    )
    discount_days = models.IntegerField(
        default=0, help_text="Días para aplicar descuento"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "payment_terms"
        verbose_name = "Término de Pago"
        verbose_name_plural = "Términos de Pago"
        ordering = ["days"]

    def __str__(self):
        return self.name
