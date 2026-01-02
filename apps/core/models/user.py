from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el email y password dados
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel, UUIDModel):
    """
    Usuario personalizado que usa email como identificador único
    """

    # Deshabilitar username de AbstractUser
    username = None

    # ✅ Validador para teléfono
    phone_validator = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message="El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos.",
    )

    # Email como identificador único
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    avatar = models.URLField(blank=True, help_text="URL de la imagen de perfil")

    # Tipos de usuarios
    USER_TYPE_CHOICES = [
        ("business_owner", "Propietario de negocio"),
        ("employee", "Empleado"),
        ("customer", "Cliente"),
        ("admin", "Administrador"),
    ]
    user_type = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="customer", db_index=True
    )

    # Verificación
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    # Manager personalizado
    objects = UserManager()

    # Configuración de autenticación
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]  # Campos requeridos además de email y password

    class Meta:
        db_table = "users"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["user_type"]),
            models.Index(fields=["is_active", "email_verified"]),
        ]

    def __str__(self):
        return self.email

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        # Validar que el email no esté vacío
        if not self.email:
            raise ValidationError({"email": "El email es obligatorio"})

        # Normalizar email
        self.email = self.email.lower().strip()

        # Validar teléfono si se proporciona
        if self.phone:
            self.phone = self.phone.strip()

    @property
    def full_name(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        """Retorna el nombre corto del usuario"""
        return self.first_name

    def get_businesses(self):
        """Retorna los negocios donde el usuario es miembro activo"""
        return Business.objects.filter(
            members__user=self, members__is_active=True
        ).distinct()

    def is_member_of(self, business):
        """Verifica si el usuario es miembro de un negocio"""
        return self.business_memberships.filter(
            business=business, is_active=True
        ).exists()

    def get_role_in_business(self, business):
        """Obtiene el rol del usuario en un negocio específico"""
        try:
            membership = self.business_memberships.get(
                business=business, is_active=True
            )
            return membership.role
        except:
            return None

    def has_permission_in_business(self, business, permission_key):
        """Verifica si el usuario tiene un permiso específico en un negocio"""
        try:
            membership = self.business_memberships.get(
                business=business, is_active=True
            )
            return membership.has_permission(permission_key)
        except:
            return False


class BusinessMember(TimeStampedModel, UUIDModel):
    """
    Relación entre un usuario y un negocio (membresía)
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="business_memberships"
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name="members"
    )

    # Roles
    ROLE_CHOICES = [
        ("owner", "Propietario"),
        ("admin", "Administrador"),
        ("manager", "Gerente"),
        ("employee", "Empleado"),
        ("cashier", "Cajero"),
    ]
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default="employee", db_index=True
    )

    # ✅ Estructura de permisos mejorada
    permissions = models.JSONField(
        default=dict, help_text="Diccionario de permisos específicos por módulo"
    )
    # Ejemplo de estructura:
    # {
    #   "orders": {"create": True, "read": True, "update": True, "delete": False},
    #   "products": {"create": True, "read": True, "update": True, "delete": False},
    #   "customers": {"create": True, "read": True, "update": True, "delete": False},
    #   "inventory": {"create": False, "read": True, "update": False, "delete": False},
    #   "finance": {"create": False, "read": False, "update": False, "delete": False},
    #   "reports": {"read": False}
    # }

    # Estado del miembro
    is_active = models.BooleanField(
        default=True, help_text="Si el miembro está activo en el negocio"
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que invitó a este miembro",
        related_name="invited_members",
    )
    invitation_accepted_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha en que el miembro aceptó la invitación"
    )

    class Meta:
        db_table = "business_members"
        verbose_name = "Miembro del Negocio"
        verbose_name_plural = "Miembros del Negocio"
        unique_together = ("user", "business")
        ordering = ["role", "user__first_name"]
        indexes = [
            models.Index(fields=["business", "role"]),
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["business", "is_active", "role"]),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.business.name} ({self.role})"

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        # ✅ No puede haber dos owners en el mismo negocio
        if self.role == "owner":
            existing_owner = BusinessMember.objects.filter(
                business=self.business, role="owner", is_active=True
            ).exclude(pk=self.pk)

            if existing_owner.exists():
                raise ValidationError(
                    "Ya existe un propietario para este negocio. "
                    "Debes transferir la propiedad primero."
                )

    @property
    def is_admin(self):
        """Verifica si el miembro es admin u owner"""
        return self.role in ["owner", "admin"]

    def has_permission(self, permission_key):
        """Verifica si el miembro tiene un permiso específico"""
        if self.role == "owner":
            return True  # Owner tiene todos los permisos

        # Verificar en el diccionario de permisos
        # permission_key formato: "orders.create", "products.read", etc.
        try:
            module, action = permission_key.split(".")
            return self.permissions.get(module, {}).get(action, False)
        except:
            return False

    def set_default_permissions_by_role(self):
        """Establece permisos por defecto según el rol"""
        # ✅ Permisos por defecto según el rol
        default_permissions = {
            "owner": {
                "orders": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "products": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "customers": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "inventory": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "finance": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "reports": {"read": True},
                "settings": {"update": True},
            },
            "admin": {
                "orders": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "products": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "customers": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                },
                "inventory": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "finance": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "reports": {"read": True},
                "settings": {"update": False},
            },
            "manager": {
                "orders": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "products": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "customers": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "inventory": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "finance": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "reports": {"read": True},
                "settings": {"update": False},
            },
            "employee": {
                "orders": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "products": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "customers": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": False,
                },
                "inventory": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "finance": {
                    "create": False,
                    "read": False,
                    "update": False,
                    "delete": False,
                },
                "reports": {"read": False},
                "settings": {"update": False},
            },
            "cashier": {
                "orders": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "products": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "customers": {
                    "create": True,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "inventory": {
                    "create": False,
                    "read": True,
                    "update": False,
                    "delete": False,
                },
                "finance": {
                    "create": False,
                    "read": False,
                    "update": False,
                    "delete": False,
                },
                "reports": {"read": False},
                "settings": {"update": False},
            },
        }

        self.permissions = default_permissions.get(self.role, {})
        self.save(update_fields=["permissions", "updated_at"])


class Customer(TimeStampedModel, UUIDModel):
    """
    Cliente de un negocio específico
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="Usuario asociado al cliente"
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        help_text="Negocio al que pertenece el cliente",
    )

    # Identificación del cliente
    customer_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número único de identificación del cliente",
    )

    # Notas
    notes = models.TextField(
        blank=True, null=True, help_text="Notas adicionales sobre el cliente"
    )

    # Sistema de Lealtad
    loyalty_points = models.IntegerField(default=0)

    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Total gastado por el cliente",
    )

    total_orders = models.IntegerField(
        default=0, help_text="Número total de órdenes del cliente"
    )

    # Estados
    is_vip = models.BooleanField(default=False, help_text="Si el cliente es VIP")
    is_blocked = models.BooleanField(
        default=False, help_text="Si el cliente está bloqueado"
    )

    # Preferencias de contacto
    prefer_email = models.BooleanField(
        default=True, help_text="Preferir contacto por email"
    )
    prefer_sms = models.BooleanField(
        default=False, help_text="Preferir contacto por SMS"
    )

    # Fechas Importantes
    first_purchase_date = models.DateTimeField(
        null=True, blank=True, help_text="Fecha de la primera compra del cliente"
    )
    last_purchase_date = models.DateTimeField(
        null=True, blank=True, help_text="Fecha de la última compra del cliente"
    )

    class Meta:
        db_table = "customers"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        unique_together = [["user", "business"]]
        indexes = [
            models.Index(fields=["business", "is_vip"]),
            models.Index(fields=["business", "total_spent"]),
            models.Index(fields=["customer_number"]),
        ]

    def __str__(self):
        return f"{self.user.full_name} @ {self.business.name}"

    def save(self, *args, **kwargs):
        """Auto-genera customer_number si no existe"""
        if not self.customer_number:
            last_customer = (
                Customer.objects.filter(business=self.business)
                .order_by("-customer_number")
                .first()
            )

            if last_customer and last_customer.customer_number:
                try:
                    last_number = int(last_customer.customer_number.split("-")[1])
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
        self.save(update_fields=["loyalty_points", "updated_at"])

    def redeem_loyalty_points(self, points):
        """Redime puntos de lealtad"""
        if self.loyalty_points >= points:
            self.loyalty_points -= points
            self.save(update_fields=["loyalty_points", "updated_at"])
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

        # ✅ Auto-promoción a VIP si gasta más de X
        if self.total_spent >= 1000000:  # 1 millón COP
            self.is_vip = True

        self.save(
            update_fields=[
                "total_spent",
                "total_orders",
                "last_purchase_date",
                "first_purchase_date",
                "is_vip",
                "updated_at",
            ]
        )
