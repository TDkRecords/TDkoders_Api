from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models.base import TimeStampedModel, UUIDModel
from apps.core.models import Business, User, Customer, Product, ProductVariant


class DailySummary(TimeStampedModel, UUIDModel):
    """
    Resumen diario de métricas del negocio.

    ¿Para qué?
    - Pre-calcular métricas para dashboards rápidos
    - Evitar consultas pesadas en reportes
    - Análisis de tendencias
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="daily_summaries"
    )

    # Fecha
    date = models.DateField(help_text="Fecha del resumen")

    # Ventas
    total_sales = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Total de ventas del día",
    )
    total_orders = models.IntegerField(default=0, help_text="Número de órdenes")
    average_order_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Valor promedio por orden",
    )

    # Productos
    products_sold = models.IntegerField(
        default=0, help_text="Cantidad de productos vendidos"
    )

    # Clientes
    new_customers = models.IntegerField(default=0, help_text="Clientes nuevos del día")
    returning_customers = models.IntegerField(
        default=0, help_text="Clientes recurrentes"
    )

    # Gastos
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Ganancias
    gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Ganancia bruta (ventas - costo de productos)",
    )
    net_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Ganancia neta (ganancia bruta - gastos)",
    )

    # Reservas (si aplica)
    total_reservations = models.IntegerField(default=0)
    completed_reservations = models.IntegerField(default=0)
    cancelled_reservations = models.IntegerField(default=0)

    # Inventario
    low_stock_items = models.IntegerField(default=0, help_text="Items con bajo stock")
    out_of_stock_items = models.IntegerField(default=0, help_text="Items sin stock")

    class Meta:
        db_table = "daily_summaries"
        verbose_name = "Resumen Diario"
        verbose_name_plural = "Resúmenes Diarios"
        unique_together = [["business", "date"]]
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["business", "date"]),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.date}"


class ProductAnalytics(TimeStampedModel, UUIDModel):
    """
    Analíticas por producto.

    ¿Para qué?
    - Identificar productos más vendidos
    - Análisis de rentabilidad por producto
    - Optimizar inventario
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="product_analytics"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="analytics"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analytics",
    )

    # Período
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Diario"),
            ("weekly", "Semanal"),
            ("monthly", "Mensual"),
            ("yearly", "Anual"),
        ],
        default="monthly",
    )

    # Ventas
    units_sold = models.IntegerField(default=0, help_text="Unidades vendidas")
    total_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, help_text="Ingresos totales"
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, help_text="Costo total"
    )
    gross_profit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00, help_text="Ganancia bruta"
    )

    # Métricas
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Margen de ganancia en porcentaje",
    )

    # Inventario
    stock_turnover_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Tasa de rotación de inventario",
    )
    days_out_of_stock = models.IntegerField(
        default=0, help_text="Días sin stock en el período"
    )

    # Ranking
    sales_rank = models.IntegerField(
        null=True, blank=True, help_text="Ranking de ventas"
    )

    class Meta:
        db_table = "product_analytics"
        verbose_name = "Analítica de Producto"
        verbose_name_plural = "Analíticas de Productos"
        unique_together = [
            ["business", "product", "variant", "period_start", "period_end"]
        ]
        ordering = ["-period_start", "-total_revenue"]
        indexes = [
            models.Index(fields=["business", "period_start", "period_end"]),
            models.Index(fields=["product", "period_type"]),
        ]

    def __str__(self):
        variant_str = f" - {self.variant.name}" if self.variant else ""
        return f"{self.product.name}{variant_str} ({self.period_start} - {self.period_end})"


class CustomerAnalytics(TimeStampedModel, UUIDModel):
    """
    Analíticas por cliente.

    ¿Para qué?
    - Identificar mejores clientes
    - Análisis de comportamiento de compra
    - Segmentación de clientes
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="customer_analytics"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="analytics"
    )

    # Período
    period_start = models.DateField()
    period_end = models.DateField()

    # Compras
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )

    # Frecuencia
    purchase_frequency = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Compras por mes"
    )
    days_since_last_purchase = models.IntegerField(
        default=0, help_text="Días desde última compra"
    )

    # Productos favoritos
    favorite_products = models.JSONField(
        default=list, help_text="Lista de productos más comprados"
    )

    # Categorías preferidas
    favorite_categories = models.JSONField(
        default=list, help_text="Categorías más compradas"
    )

    # RFM Analysis (Recency, Frequency, Monetary)
    rfm_recency_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score de recencia (1-5)",
    )
    rfm_frequency_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score de frecuencia (1-5)",
    )
    rfm_monetary_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score monetario (1-5)",
    )
    rfm_segment = models.CharField(
        max_length=50,
        blank=True,
        help_text="Segmento RFM (ej: Champions, Loyal, At Risk)",
    )

    # CLV (Customer Lifetime Value)
    lifetime_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Valor total del cliente",
    )
    predicted_lifetime_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Valor predicho del cliente",
    )

    class Meta:
        db_table = "customer_analytics"
        verbose_name = "Analítica de Cliente"
        verbose_name_plural = "Analíticas de Clientes"
        unique_together = [["business", "customer", "period_start", "period_end"]]
        ordering = ["-total_spent"]
        indexes = [
            models.Index(fields=["business", "period_start", "period_end"]),
            models.Index(fields=["customer", "period_start"]),
            models.Index(fields=["rfm_segment"]),
        ]

    def __str__(self):
        return f"{self.customer.user.full_name} - {self.period_start}"


class SalesReport(TimeStampedModel, UUIDModel):
    """
    Reportes de ventas pre-generados.

    ¿Para qué?
    - Reportes mensuales/anuales listos para imprimir
    - Auditoría y registros históricos
    - Análisis comparativo entre períodos
    """

    REPORT_TYPE_CHOICES = [
        ("daily", "Reporte Diario"),
        ("weekly", "Reporte Semanal"),
        ("monthly", "Reporte Mensual"),
        ("quarterly", "Reporte Trimestral"),
        ("yearly", "Reporte Anual"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="sales_reports"
    )

    # Tipo y período
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()

    # Ventas
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_orders = models.IntegerField(default=0)
    total_items_sold = models.IntegerField(default=0)

    # Comparación con período anterior
    sales_growth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Crecimiento en porcentaje",
    )

    # Top productos
    top_products = models.JSONField(
        default=list, help_text="Lista de productos más vendidos"
    )

    # Top clientes
    top_customers = models.JSONField(
        default=list, help_text="Lista de mejores clientes"
    )

    # Datos detallados
    detailed_data = models.JSONField(
        default=dict, help_text="Datos detallados del reporte"
    )

    # Usuario que generó el reporte
    generated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="generated_reports"
    )

    class Meta:
        db_table = "sales_reports"
        verbose_name = "Reporte de Ventas"
        verbose_name_plural = "Reportes de Ventas"
        unique_together = [["business", "report_type", "period_start", "period_end"]]
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["business", "report_type"]),
            models.Index(fields=["period_start", "period_end"]),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start} a {self.period_end}"


class BusinessMetrics(TimeStampedModel, UUIDModel):
    """
    Métricas clave del negocio (KPIs).

    ¿Para qué?
    - Dashboard ejecutivo
    - Seguimiento de objetivos
    - Toma de decisiones estratégicas
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="metrics"
    )

    # Período
    period_start = models.DateField()
    period_end = models.DateField()

    # Ventas
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    revenue_growth = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, help_text="Crecimiento en %"
    )

    # Rentabilidad
    gross_profit_margin = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="Margen bruto en %"
    )
    net_profit_margin = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="Margen neto en %"
    )

    # Clientes
    total_customers = models.IntegerField(default=0)
    new_customers = models.IntegerField(default=0)
    customer_retention_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="Tasa de retención en %"
    )
    customer_churn_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="Tasa de abandono en %"
    )

    # Órdenes
    average_order_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00
    )
    order_fulfillment_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tasa de cumplimiento en %",
    )

    # Inventario
    inventory_turnover = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Rotación de inventario",
    )
    days_inventory_outstanding = models.IntegerField(
        default=0, help_text="Días de inventario disponible"
    )

    # Eficiencia
    cost_per_acquisition = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Costo por adquisición de cliente",
    )

    class Meta:
        db_table = "business_metrics"
        verbose_name = "Métrica del Negocio"
        verbose_name_plural = "Métricas del Negocio"
        unique_together = [["business", "period_start", "period_end"]]
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["business", "period_start", "period_end"]),
        ]

    def __str__(self):
        return (
            f"{self.business.name} - Métricas {self.period_start} a {self.period_end}"
        )


class CategoryPerformance(TimeStampedModel, UUIDModel):
    """
    Rendimiento por categoría de productos.

    ¿Para qué?
    - Identificar categorías exitosas
    - Optimizar mix de productos
    - Planificar inventario
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="category_performance"
    )
    category = models.ForeignKey(
        "core.Category", on_delete=models.CASCADE, related_name="performance"
    )

    # Período
    period_start = models.DateField()
    period_end = models.DateField()

    # Ventas
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    units_sold = models.IntegerField(default=0)

    # Porcentaje del total
    sales_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, help_text="% del total de ventas"
    )

    # Rentabilidad
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # Crecimiento
    sales_growth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Crecimiento vs período anterior",
    )

    class Meta:
        db_table = "category_performance"
        verbose_name = "Rendimiento de Categoría"
        verbose_name_plural = "Rendimiento de Categorías"
        unique_together = [["business", "category", "period_start", "period_end"]]
        ordering = ["-total_sales"]
        indexes = [
            models.Index(fields=["business", "period_start", "period_end"]),
            models.Index(fields=["category", "period_start"]),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.period_start}"
