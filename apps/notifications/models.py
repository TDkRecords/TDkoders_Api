from django.db import models
from apps.core.models.base import TimeStampedModel, UUIDModel, SoftDeleteModel
from apps.core.models import Business, User

# Create your models here.


class Notification(TimeStampedModel, UUIDModel, SoftDeleteModel):

    TYPE_CHOICES = [
        ("system", "Sistema"),
        ("order", "Orden"),
        ("reservation", "Reserva"),
        ("inventory", "Inventario"),
        ("finance", "Finanzas"),
    ]

    CHANNEL_CHOICES = [
        ("in_app", "In-App"),
        ("email", "Email"),
        ("sms", "SMS"),
        ("push", "Push"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Baja"),
        ("normal", "Normal"),
        ("high", "Alta"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Negocio al que pertenece la notificación",
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Usuario destinatario",
    )

    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)

    notification_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default="system"
    )
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="in_app")
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="normal"
    )

    url = models.URLField(blank=True, help_text="URL de destino en el frontend")
    metadata = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "recipient", "is_read"]),
            models.Index(fields=["notification_type", "channel"]),
            models.Index(fields=["priority", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"

    def mark_read(self):
        from django.utils import timezone

        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at", "updated_at"])


class NotificationPreference(TimeStampedModel, UUIDModel):

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        help_text="Negocio para el que aplican las preferencias",
    )

    allow_in_app = models.BooleanField(default=True)
    allow_email = models.BooleanField(default=False)
    allow_sms = models.BooleanField(default=False)
    allow_push = models.BooleanField(default=False)

    muted_types = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de tipos silenciados (ej: ["inventory", "finance"])',
    )

    is_muted = models.BooleanField(
        default=False, help_text="Silenciar todas las notificaciones para este negocio"
    )
    quiet_hours = models.JSONField(
        default=dict,
        blank=True,
        help_text='Horario de silencio (ej: {"start": "22:00", "end": "07:00"})',
    )

    class Meta:
        db_table = "notification_preferences"
        verbose_name = "Preferencia de Notificación"
        verbose_name_plural = "Preferencias de Notificación"
        unique_together = [["user", "business"]]
        indexes = [
            models.Index(fields=["user", "business"]),
        ]

    def __str__(self):
        return f"Preferencias de {self.user.email} @ {self.business.name}"
