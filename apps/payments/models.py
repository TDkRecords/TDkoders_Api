from django.db import models
from apps.core.models.base import TimeStampedModel, UUIDModel, SoftDeleteModel
from apps.core.models import Business, User
from apps.finance.models import Invoice
from apps.orders.models import Order


class Payment(TimeStampedModel, UUIDModel, SoftDeleteModel):
    PROVIDER_CHOICES = [
        ("manual", "Manual"),
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
        ("mercadopago", "MercadoPago"),
        ("other", "Otro"),
    ]

    METHOD_CHOICES = [
        ("cash", "Efectivo"),
        ("card", "Tarjeta"),
        ("transfer", "Transferencia"),
        ("online", "Pago Online"),
        ("other", "Otro"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("authorized", "Autorizado"),
        ("captured", "Capturado"),
        ("failed", "Fallido"),
        ("refunded", "Reembolsado"),
        ("cancelled", "Cancelado"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="payments"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
    )

    payment_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="COP")
    provider = models.CharField(
        max_length=20, choices=PROVIDER_CHOICES, default="manual"
    )
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="cash")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    external_id = models.CharField(max_length=100, blank=True)
    receipt_url = models.URLField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_payments"
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "status"]),
            models.Index(fields=["provider", "created_at"]),
        ]

    def __str__(self):
        return self.payment_number

    def save(self, *args, **kwargs):
        if not self.payment_number:
            from django.utils import timezone

            date_str = timezone.now().strftime("%Y%m%d")
            last_payment = (
                Payment.objects.filter(
                    business=self.business, payment_number__startswith=f"PAY-{date_str}"
                )
                .order_by("-payment_number")
                .first()
            )
            if last_payment:
                try:
                    last_num = int(last_payment.payment_number.split("-")[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.payment_number = f"PAY-{date_str}-{new_num:04d}"
        super().save(*args, **kwargs)


class PaymentWebhookEvent(TimeStampedModel, UUIDModel):
    PROVIDER_CHOICES = [
        ("stripe", "Stripe"),
        ("paypal", "PayPal"),
        ("mercadopago", "MercadoPago"),
        ("other", "Otro"),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="payment_webhook_events"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    event_type = models.CharField(max_length=100)
    external_id = models.CharField(max_length=100, unique=True)
    payload = models.JSONField(default=dict, blank=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "payment_webhook_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["business", "provider"]),
            models.Index(fields=["event_type"]),
        ]
