from enum import unique
from django.contrib.auth.models import AbstractUser
from django.db import models
from .base import TimeStampedModel, UUIDModel
from .business import Business

class User(AbstractUser, TimeStampedModel, UUIDModel):
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    avatar = models.URLField(blank=True, help_text="URL de la imagen de perfil")
    
    # Tipos de usuarios
    USER_TYPE_CHOICES = [
        ('business_owner', 'Propietario de negocio'),
        ('employee', 'Empleado'),
        ('customer', 'Cliente'),
        ('admin', 'Administrador'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    
    # Verificación
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Configuración de autenticación
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def __str__(self):
        return self.username or self.email
    
    class Meta:
        db_table = 'users'
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
        ]
        
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
class BusinessMember(TimeStampedModel, UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_memberships')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='members')
    
    # Roles
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('employee', 'Empleado'),
        ('cashier', 'Cajero'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    
    # Permisos especificos
    permissions = models.JSONField(
        default=dict, 
        help_text="Diccionario de permisos específicos por módulo (ej: {'ventas': ['ver', 'crear'], 'inventario': ['ver']})"
    )
    
    # Estado del miembro
    is_active = models.BooleanField(
        default=True, 
        help_text="Si el miembro está activo en el negocio"
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Usuario que invitó a este miembro",
        related_name='invited_members'
    )
    invitation_accepted_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Fecha en que el miembro aceptó la invitación"
    )
    
    class Meta:
        db_table = "business_members"
        verbose_name = "Miembro del Negocio"
        verbose_name_plural = "Miembros del Negocio"
        unique_together = ('user', 'business')
        ordering = ['role', 'user__first_name']
        
        indexes = [
            models.Index(fields=['business', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.business.name} ({self.role})"
    
    @property
    def is_admin(self):
        return self.role in ['owner', 'admin']
    
    def has_permission(self, permission_key):
        if self.is_owner:
            return True
        return self.permissions.get(permission_key, False)
        
class Customer(TimeStampedModel, UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Usuario asociado al cliente")
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        help_text="Negocio al que pertenece el cliente"
    )
    
    # Identificación del cliente
    customer_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número único de identificación del cliente"
    )
    
    # Notas
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales sobre el cliente"
    )
    
    # Sistema de Lealtad
    loyality_points = models.IntegerField(default=0)
    
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total gastado por el cliente"
    )
    
    total_orders = models.IntegerField(default=0, help_text="Número total de órdenes del cliente")
    
    # Estados
    is_vip = models.BooleanField(default=False, help_text="Si el cliente es VIP")
    is_blocked = models.BooleanField(default=False, help_text="Si el cliente está bloqueado")
    
    # Preferencias de contacto
    prefer_email = models.BooleanField(default=True, help_text="Preferir contacto por email")
    prefer_sms = models.BooleanField(default=False, help_text="Preferir contacto por SMS")
    
    # Fechas Importantes
    first_purchase_date = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Fecha de la primera compra del cliente"
    )
    last_purchase_date = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Fecha de la última compra del cliente"
    )
    
    class Meta:
        db_table = 'customers'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        unique_together = [['user', 'business']]
        
        indexes = [
            models.Index(fields=['business', 'is_vip']),
            models.Index(fields=['business', 'total_spent']),
        ]
        
    def __str__(self):
        return f"{self.user.full_name} @ {self.business.name}"
    
    def save(self, *args, **kwargs):
        if not self.customer_number:
            last_customer  = Customer.objects.filter(
                business=self.business
            ).order_by('-customer_number').first()
            
            if last_customer and last_customer.customer_number:
                try:
                    last_number = int(last_customer.customer_number.split('-')[1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            prefix = self.business.slug.upper()[:3]
            self.customer_number = f"{prefix}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    # Agrega puntos de lealtad
    def add_loyalty_points(self, points):
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points', 'updated_at'])
        
    # Redime puntos de lealtad
    def redeem_loyalty_points(self, points):
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=['loyalty_points', 'updated_at'])
            return True
        return False
    
    # Actualiza estadísticas de compras
    def update_purchase_stats(self, order_total):
        from django.utils import timezone
        
        self.total_spent += order_total
        self.total_orders += 1
        self.last_purchase_date = timezone.now()
        
        if not self.first_purchase_date:
            self.first_purchase_date = timezone.now()
        
        self.save(update_fields=[
            'total_spent',
            'total_orders',
            'last_purchase_date',
            'first_purchase_date',
            'updated_at'
        ])
    