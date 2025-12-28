from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from .base import TimeStampedModel, UUIDModel, SoftDeleteModel
from uuid import uuid4


class BusinessType(TimeStampedModel, UUIDModel):
    name = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="Tipo de negocio: Restaurante, Barberia, Hotel, etc."
    )
    
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    
    has_inventory = models.BooleanField(
        default=True,  # La mayoría SÍ maneja inventario
        help_text="¿Este negocio maneja inventario físico?"
    )
    
    has_reservations = models.BooleanField(
        default=False,  # Solo algunos manejan citas
        help_text="¿Este negocio maneja reservas/citas?"
    )
    
    has_services = models.BooleanField(
        default=False,
        help_text="¿Este negocio ofrece servicios?"
    )
    
    has_variants = models.BooleanField(
        default=True,  # La mayoría tiene variantes (tallas, pesos, etc)
        help_text="¿Los productos tienen variantes (tallas, pesos, etc)?"
    )
    
    default_attributes = models.JSONField(
        default=list,
        blank=True,
        help_text='Ej: ["Talla", "Color"] para tienda de ropa'
    )
    
    class Meta:
        db_table = "business_types"
        verbose_name = "Tipo de Negocio"
        verbose_name_plural = "Tipos de Negocios"
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.name)}-{uuid4().hex[:6]}"
        super().save(*args, **kwargs)
    
class Business(TimeStampedModel, UUIDModel, SoftDeleteModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    business_type = models.ForeignKey(
        BusinessType, 
        on_delete=models.PROTECT, 
        related_name="businesses"
    )
    
    # contacto
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)  # NUEVO
    
    # Ubicación
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Logo
    logo = models.URLField(
        blank=True,
        help_text="URL del logo en S3/Cloudinary (NO subir a Django)"
    )
    
    # Configuración Regional
    timezone = models.CharField(
        max_length=50,
        default='America/Bogota',
        help_text="Timezone para fechas y horarios"
    )
    currency = models.CharField(
        max_length=3,
        default='COP',
        help_text="Código ISO de moneda (COP, USD, MXN)"
    )
    
    # Stripe
    stripe_account_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID de cuenta conectada de Stripe"
    )
    stripe_onboarding_complete = models.BooleanField(default=False)
    
    # Suscripción y estado
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('active', 'Active'),
            ('past_due', 'Past Due'),
            ('cancelled', 'Cancelled'),
        ],
        default='trial'
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'businesses'
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"
        indexes = [
            models.Index(fields=["slug"]),  # Busqueda por slug
            models.Index(fields=['is_active', 'subscription_status']),  # Busqueda por estado y suscripcion
            models.Index(fields=['is_verified', 'subscription_status']),  # Busqueda por verificacion y suscripcion
            models.Index(fields=['trial_ends_at', 'subscription_status']),  # Busqueda por fecha de finalizacion de prueba y suscripcion
        ]
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.slug:
            self.slug = f"{slugify(self.name)}-{uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    @property
    def is_subscription_active(self):
        return self.subscription_status in ["trial", "active"]
    
class BusinessSettings(TimeStampedModel, UUIDModel, SoftDeleteModel):
    # No se que poner aqui
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name="settings"
    )
    
    # Impuestos
    tax_name = models.CharField(
        max_length=50,
        default='IVA',
        help_text="Nombre del impuesto (IVA, GST, VAT)"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje (ej: 19.00 para 19%)"
    )
    tax_included_in_price = models.BooleanField(
        default=True,
        help_text="¿El impuesto está incluido en el precio?"
    )
    
    # Pagos
    accepts_online_payments = models.BooleanField(
        default=False,
        help_text="¿El negocio acepta pagos en línea?"
    )
    accepts_cash = models.BooleanField(
        default=False,
        help_text="¿El negocio acepta pagos en efectivo?"
    )
    accepts_card = models.BooleanField(
        default=False,
        help_text="¿El negocio acepta pagos con tarjeta?"
    )
    requires_deposit = models.BooleanField(
        default=False,
        help_text="¿El negocio requiere depósito?"
    )
    deposit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[
            MinValueValidator(0), MaxValueValidator(100)
        ],
        help_text="Porcentaje (ej: 19.00 para 19%)"
    )
    
    # Config de reservas
    min_booking_notice_hours = models.IntegerField(
        default=2,
        help_text="Número mínimo de horas de aviso para reservas"
    )
    max_booking_days_advance = models.IntegerField(
        default=365,
        help_text="Número máximo de días de antelación para reservas (1 año = 365 días)"
    )
    cancellation_policy = models.IntegerField(
        default=2,
        help_text="Horas mínimas antes de la reserva para cancelar sin cargo (ej: 2 para 2 horas)"
    )
    
    # Configuración de inventario
    low_stock_threshold = models.IntegerField(
        default=5,
        help_text="Cantidad mínima para alertar de bajo stock (ej: 5 para 5 unidades)"
    )
    
    auto_detect_inventory = models.BooleanField(
        default=False,
        help_text="¿Activar detección automática de inventario? (ej: True para activar, False para desactivar)"
    )
    
    # Configuración de Notificaciones
    send_order_confirmation = models.BooleanField(
        default=False,
        help_text="¿Enviar confirmación de pedido por correo? (ej: True para activar, False para desactivar)"
    )
    
    send_reservation_confirmation = models.BooleanField(
        default=False,
        help_text="¿Enviar confirmación de reserva por correo? (ej: True para activar, False para desactivar)"
    )
    
    reminder_hours_before = models.IntegerField(
        default=8,
        help_text="Horas antes de la reserva para enviar recordatorio (ej: 8 para 8 horas antes)"
    )
    
    # Horario de operaciones
    bussines_hours = models.JSONField(
        default=dict,
        help_text="Horario de operaciones por día de la semana en formato JSON (ej: {'lunes': {'abierto': '09:00', 'cerrado': '18:00'}})",
        blank=True,
    )
    
    class Meta:
        verbose_name = "Configuración del Negocio"
        verbose_name_plural = "Configuraciones de Negocios"
        
    def __str__(self):
        return f"Configuración de {self.business.name}"