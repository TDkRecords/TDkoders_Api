from django.db import models


class BussinesType(models.Model):
    bussines_type = models.CharField(max_length=100)
    has_inventory = models.BooleanField(default=False)
    has_reservations = models.BooleanField(default=False)
    has_services = models.BooleanField(default=False)
    has_variants = models.BooleanField(default=False)
    
    def __str__(self):
        return self.bussines_type
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Tipo de Negocio"
        verbose_name_plural = "Tipos de Negocios"
    
class Business(models.Model):
    name = models.CharField(max_length=100)
    bussines_type = models.ForeignKey(BussinesType, on_delete=models.CASCADE)
    slug = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Ubicación
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Stripe
    stripe_account_id = models.CharField(max_length=100, null=True, blank=True)
    stripe_onboarding_complete = models.BooleanField(default=False)
    stripe_webhook_secret = models.CharField(max_length=100, null=True, blank=True)
    stripe_webhook_endpoint = models.CharField(max_length=100, null=True, blank=True)
    stripe_webhook_endpoint_secret = models.CharField(max_length=100, null=True, blank=True)
    
    # Suscripción
    subscription_status = models.CharField(max_length=100, null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"

class BusinessSettings(models.Model):
    # No se que poner aqui
    pass