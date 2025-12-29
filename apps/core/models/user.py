from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from .base import TimeStampedModel, UUIDModel
from .business import Business


class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User que usa email en lugar de username
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el email y password dados
        """
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el email y password dados
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel, UUIDModel):
    """
    Usuario personalizado que usa email como identificador único
    """
    # Deshabilitar username de AbstractUser
    username = None
    
    # Email como identificador único
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(blank=True, help_text="URL de la imagen de perfil")
    
    # Tipos de usuarios
    USER_TYPE_CHOICES = [
        ('business_owner', 'Propietario de negocio'),
        ('employee', 'Empleado'),
        ('customer', 'Cliente'),
        ('admin', 'Administrador'),
    ]
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPE_CHOICES, 
        default='customer'
    )
    
    # Verificación
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Manager personalizado
    objects = UserManager()
    
    # Configuración de autenticación
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Campos requeridos además de email y password
    
    class Meta:
        db_table = 'users'
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.first_name


class BusinessMember(TimeStampedModel, UUIDModel):
    """
    Relación entre un usuario y un negocio (membresía)
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='business_memberships'
    )
    business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE, 
        related_name='members'
    )
    
    # Roles
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('employee', 'Empleado'),
        ('cashier', 'Cajero'),
    ]
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='employee'
    )
    
    # Permisos específicos
    permissions = models.JSONField(
        default=dict, 
        help_text="Diccionario de permisos específicos por módulo"
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
        """Verifica si el miembro es admin u owner"""
        return self.role in ['owner', 'admin']
    
    def has_permission(self, permission_key):
        """Verifica si el miembro tiene un permiso específico"""
        if self.role == 'owner':
            return True
        return self.permissions.get(permission_key, False)


class Customer(TimeStampedModel, UUIDModel):
    """
    Cliente de un negocio específico
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        help_text="Usuario asociado al cliente"
    )
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
    loyalty_points = models.IntegerField(default=0)
    
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total gastado por el cliente"
    )
    
    total_orders = models.IntegerField(
        default=0, 
        help_text="Número total de órdenes del cliente"
    )
    
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
        """Auto-genera customer_number si no existe"""
        if not self.customer_number:
            last_customer = Customer.objects.filter(
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
    
    def add_loyalty_points(self, points):
        """Agrega puntos de lealtad"""
        self.loyalty_points += points
        self.save(update_fields=['loyalty_points', 'updated_at'])
        
    def redeem_loyalty_points(self, points):
        """Redime puntos de lealtad"""
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=['loyalty_points', 'updated_at'])
            return True
        return False
    
    def update_purchase_stats(self, order_total):
        """Actualiza estadísticas de compras"""
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