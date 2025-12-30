from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.core.models.base import TimeStampedModel, UUIDModel, SoftDeleteModel
from apps.core.models import Business, User, Customer, Product


class ServiceProvider(TimeStampedModel, UUIDModel):
    """
    Proveedor de servicios (empleado que realiza servicios).

    ¿Para qué?
    - Barbero, estilista, masajista, doctor, etc.
    - Cada proveedor tiene su agenda y disponibilidad
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="service_providers"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="service_provider_profiles"
    )

    # Información
    title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Título profesional (ej: Barbero Senior, Estilista)",
    )
    bio = models.TextField(
        blank=True, help_text="Biografía o descripción del proveedor"
    )
    image_url = models.URLField(blank=True)

    # Configuración
    is_active = models.BooleanField(
        default=True, help_text="¿Está activo para recibir reservas?"
    )
    accepts_walk_ins = models.BooleanField(
        default=True, help_text="¿Acepta clientes sin cita?"
    )

    # Horario de trabajo
    working_hours = models.JSONField(
        default=dict, help_text="Horario de trabajo por día"
    )
    # Ejemplo: {
    #   "monday": {"start": "09:00", "end": "18:00", "breaks": [{"start": "13:00", "end": "14:00"}]},
    #   "tuesday": {"start": "09:00", "end": "18:00"},
    #   ...
    # }

    # Servicios que puede realizar
    # (relación con Product donde is_service=True)

    class Meta:
        db_table = "service_providers"
        verbose_name = "Proveedor de Servicio"
        verbose_name_plural = "Proveedores de Servicios"
        unique_together = [["business", "user"]]
        ordering = ["user__first_name"]

    def __str__(self):
        return f"{self.user.full_name} - {self.title or 'Proveedor'}"


class Reservation(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """
    Reserva o cita para un servicio.

    ¿Para qué?
    - Agenda de servicios (barbería, spa, consulta médica, etc.)
    - Control de disponibilidad de tiempo y personal
    """

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("confirmed", "Confirmada"),
        ("in_progress", "En Progreso"),
        ("completed", "Completada"),
        ("cancelled", "Cancelada"),
        ("no_show", "No Asistió"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="reservations"
    )

    # Número de reserva
    reservation_number = models.CharField(
        max_length=50, unique=True, help_text="Número único de reserva (auto-generado)"
    )

    # Cliente
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
    )

    # Datos del cliente (para reservas sin registro)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Proveedor de servicio
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservations",
        help_text="Empleado que realizará el servicio",
    )

    # Fecha y hora
    start_datetime = models.DateTimeField(help_text="Fecha y hora de inicio")
    end_datetime = models.DateTimeField(help_text="Fecha y hora de finalización")
    duration_minutes = models.IntegerField(help_text="Duración en minutos")

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Servicios incluidos (relación con OrderItem para detalles)
    # Los servicios se registran en ReservationService

    # Recordatorios
    reminder_sent = models.BooleanField(
        default=False, help_text="¿Se envió recordatorio?"
    )
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    # Confirmación
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_reservations",
    )

    # Cancelación
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_reservations",
    )
    cancellation_reason = models.TextField(blank=True)

    # Depósito
    requires_deposit = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deposit_paid = models.BooleanField(default=False)

    # Totales
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Monto total de la reserva",
    )

    # Responsables
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_reservations"
    )

    # Notas
    notes = models.TextField(blank=True, help_text="Notas internas")
    customer_notes = models.TextField(
        blank=True, help_text="Notas del cliente (solicitudes especiales)"
    )

    class Meta:
        db_table = "reservations"
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["-start_datetime"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["service_provider", "start_datetime"]),
            models.Index(fields=["customer", "start_datetime"]),
            models.Index(fields=["start_datetime", "end_datetime"]),
        ]

    def __str__(self):
        return f"{self.reservation_number} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        """Validar antes de guardar"""
        super().clean()

        # Validar fechas
        if self.end_datetime <= self.start_datetime:
            raise ValidationError(
                {"end_datetime": "La hora de fin debe ser posterior a la de inicio"}
            )

        # Validar que no haya solapamiento con otras reservas
        if self.service_provider:
            overlapping = Reservation.objects.filter(
                service_provider=self.service_provider,
                status__in=["pending", "confirmed", "in_progress"],
                start_datetime__lt=self.end_datetime,
                end_datetime__gt=self.start_datetime,
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError(
                    {
                        "start_datetime": "El proveedor ya tiene una reserva en este horario"
                    }
                )

    @transaction.atomic
    def confirm_reservation(self, user):
        """Confirmar reserva"""
        from django.utils import timezone

        if self.status != "pending":
            raise ValidationError("Solo se pueden confirmar reservas pendientes")

        # Verificar depósito si es requerido
        if self.requires_deposit and not self.deposit_paid:
            raise ValidationError("Se requiere el pago del depósito para confirmar")

        self.status = "confirmed"
        self.confirmed_at = timezone.now()
        self.confirmed_by = user
        self.save()

        # Registrar en historial
        ReservationStatusHistory.objects.create(
            reservation=self,
            previous_status="pending",
            new_status="confirmed",
            changed_by=user,
        )

    def save(self, *args, **kwargs):
        """Auto-genera reservation_number"""
        if not self.reservation_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_reservation = (
                Reservation.objects.filter(
                    business=self.business,
                    reservation_number__startswith=f"RES-{date_str}",
                )
                .order_by("-reservation_number")
                .first()
            )

            if last_reservation:
                try:
                    last_num = int(last_reservation.reservation_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1

            self.reservation_number = f"RES-{date_str}-{new_num:04d}"

        super().save(*args, **kwargs)

    @property
    def is_past(self):
        """¿La reserva ya pasó?"""
        from django.utils import timezone

        return self.end_datetime < timezone.now()

    @property
    def is_upcoming(self):
        """¿La reserva es próxima (en las próximas 24 horas)?"""
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        return now < self.start_datetime < (now + timedelta(hours=24))

    def calculate_total(self):
        """Calcula el total de la reserva basado en los servicios"""
        services = self.services.all()
        self.total_amount = sum(service.total for service in services)
        self.save(update_fields=["total_amount", "updated_at"])


class ReservationService(TimeStampedModel, UUIDModel):
    """
    Servicios incluidos en una reserva.

    ¿Para qué?
    - Una reserva puede incluir múltiples servicios
    - Ejemplo: Corte + Barba + Tinte
    """

    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="services"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="reservation_services",
        help_text="Servicio (Product donde is_service=True)",
    )

    # Cantidad (usualmente 1 para servicios)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    # Precio
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del servicio al momento de la reserva",
    )

    # Duración
    duration_minutes = models.IntegerField(help_text="Duración estimada del servicio")

    # Descuentos
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Total
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "reservation_services"
        verbose_name = "Servicio de Reserva"
        verbose_name_plural = "Servicios de Reserva"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

    def save(self, *args, **kwargs):
        """Calcula el total automáticamente"""
        self.total = (self.unit_price * self.quantity) - self.discount_amount
        super().save(*args, **kwargs)


class ReservationStatusHistory(TimeStampedModel, UUIDModel):
    """
    Historial de cambios de estado de la reserva.

    ¿Para qué?
    - Trazabilidad completa de la reserva
    """

    reservation = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, related_name="status_history"
    )

    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)

    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "reservation_status_history"
        verbose_name = "Historial de Estado de Reserva"
        verbose_name_plural = "Historial de Estados de Reservas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reservation.reservation_number}: {self.previous_status} → {self.new_status}"


class ServiceProviderAvailability(TimeStampedModel, UUIDModel):
    """
    Disponibilidad especial del proveedor de servicios.

    ¿Para qué?
    - Bloquear tiempos específicos (vacaciones, días libres)
    - Agregar disponibilidad extra
    - Manejar excepciones al horario normal
    """

    AVAILABILITY_TYPE_CHOICES = [
        ("available", "Disponible"),
        ("unavailable", "No Disponible"),
        ("blocked", "Bloqueado"),
    ]

    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.CASCADE,
        related_name="availability_exceptions",
    )

    # Fecha y hora
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    # Tipo
    availability_type = models.CharField(
        max_length=20, choices=AVAILABILITY_TYPE_CHOICES
    )

    # Razón
    reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Razón de la excepción (ej: Vacaciones, Evento especial)",
    )

    # ¿Se repite?
    is_recurring = models.BooleanField(
        default=False, help_text="¿Esta excepción se repite?"
    )
    recurring_pattern = models.JSONField(
        default=dict,
        blank=True,
        help_text="Patrón de repetición (semanal, mensual, etc.)",
    )

    class Meta:
        db_table = "service_provider_availability"
        verbose_name = "Disponibilidad de Proveedor"
        verbose_name_plural = "Disponibilidad de Proveedores"
        ordering = ["start_datetime"]
        indexes = [
            models.Index(fields=["service_provider", "start_datetime", "end_datetime"]),
        ]

    def __str__(self):
        return f"{self.service_provider} - {self.get_availability_type_display()}"


class WaitingList(TimeStampedModel, UUIDModel):
    """
    Lista de espera para servicios.

    ¿Para qué?
    - Cuando no hay disponibilidad inmediata
    - Notificar a clientes cuando haya un espacio disponible
    """

    STATUS_CHOICES = [
        ("waiting", "En Espera"),
        ("notified", "Notificado"),
        ("scheduled", "Agendado"),
        ("cancelled", "Cancelado"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="waiting_lists"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="waiting_lists"
    )
    service_provider = models.ForeignKey(
        ServiceProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waiting_lists",
    )

    # Servicio deseado
    desired_service = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Fecha/hora preferida
    preferred_date = models.DateField(
        null=True, blank=True, help_text="Fecha preferida (opcional)"
    )
    preferred_time = models.TimeField(
        null=True, blank=True, help_text="Hora preferida (opcional)"
    )

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")

    # Notificación
    notified_at = models.DateTimeField(null=True, blank=True)

    # Notas
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "waiting_lists"
        verbose_name = "Lista de Espera"
        verbose_name_plural = "Listas de Espera"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["service_provider", "status"]),
        ]

    def __str__(self):
        return f"{self.customer.user.full_name} - {self.get_status_display()}"
