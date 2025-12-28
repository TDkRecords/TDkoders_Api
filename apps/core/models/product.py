# apps/core/models/product.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from .base import TimeStampedModel, UUIDModel, SoftDeleteModel
from .business import Business


class Category(TimeStampedModel, UUIDModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    # Jerarquía (categorías anidadas)
    parent = models.ForeignKey(
        'self',  # ← Self-reference para categorías anidadas
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    # Orden de visualización
    order = models.IntegerField(default=0)
    
    # Estado
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        unique_together = [['business', 'slug']]
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['business', 'is_active']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedModel, UUIDModel, SoftDeleteModel):
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Información básica
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    # Tipo de producto
    PRODUCT_TYPE_CHOICES = [
        ('physical', 'Physical Product'),
        ('service', 'Service'),
        ('digital', 'Digital Product'),
    ]
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='physical'
    )
    
    # ¿Es un servicio? (para reservas)
    is_service = models.BooleanField(
        default=False,
        help_text="Si es True, este producto puede ser reservado"
    )
    
    # Duración del servicio
    service_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duración en minutos (ej: 30 para corte de pelo)"
    )
    
    # SKU base
    sku = models.CharField(
        max_length=100,
        blank=True,
        help_text="SKU base del producto"
    )
    
    # Imágenes
    image_url = models.URLField(
        blank=True,
        help_text="URL de la imagen principal en S3"
    )
    images = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de URLs de imágenes adicionales'
    )
    
    # Precio base (si NO tiene variantes)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    
    # Inventario (solo si NO tiene variantes)
    track_inventory = models.BooleanField(
        default=True,
        help_text="¿Controlar inventario para este producto?"
    )
    stock_quantity = models.IntegerField(
        default=0,
        help_text="Cantidad en stock (solo si no tiene variantes)"
    )
    
    # ¿Tiene variantes?
    has_variants = models.BooleanField(
        default=False,
        help_text="Si True, el producto tiene variantes (tallas, colores, etc)"
    )
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False,
        help_text="¿Mostrar como destacado?"
    )
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        unique_together = [['business', 'slug']]
        indexes = [
            models.Index(fields=['business', 'is_active']),
            models.Index(fields=['business', 'category']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-genera slug único"""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(
                business=self.business,
                slug=slug
            ).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        """Verifica si hay stock disponible"""
        if not self.track_inventory:
            return True
        
        # Si tiene variantes, verificar si alguna tiene stock
        if self.has_variants:
            return self.variants.filter(
                is_active=True,
                stock_quantity__gt=0
            ).exists()
        
        return self.stock_quantity > 0

    @property
    def price(self):
        """Retorna el precio (base o de la primera variante)"""
        if self.has_variants:
            first_variant = self.variants.filter(is_active=True).first()
            return first_variant.price if first_variant else self.base_price
        return self.base_price


class ProductVariant(TimeStampedModel, UUIDModel, SoftDeleteModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    
    # Identificación
    name = models.CharField(
        max_length=255,
        help_text="Nombre de la variante (ej: 'Talla M - Color Rojo')"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="SKU único de la variante"
    )
    
    # CAMPO CLAVE: Atributos flexibles
    # Este es el CORE del sistema agnóstico
    # Almacena los atributos específicos de esta variante en formato JSON
    # Ejemplo: {"Talla": "M", "Color": "Azul"} para ropa
    attributes = models.JSONField(
        default=dict,
        help_text='Atributos específicos de esta variante'
    )
    # Ejemplos:
    # Ropa: {"Talla": "M", "Color": "Azul"}
    # Alimentos: {"Peso": "500g", "Marca": "Diana"}
    # Servicios: {"Duración": "30min", "Barbero": "Juan"}
    
    # Precio
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Precio de comparación (para descuentos)
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Precio antes del descuento"
    )
    
    # Costo (para margen)
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Costo de adquisición"
    )
    
    # Inventario
    stock_quantity = models.IntegerField(
        default=0,
        help_text="Cantidad disponible"
    )
    
    # Imagen específica
    image_url = models.URLField(
        blank=True,
        help_text="URL de imagen específica para esta variante"
    )
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(
        default=False,
        help_text="¿Es la variante por defecto?"
    )
    
    # Orden
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Variante de Producto'
        verbose_name_plural = 'Variantes de Productos'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def is_in_stock(self):
        """Verifica si hay stock"""
        if not self.product.track_inventory:
            return True
        return self.stock_quantity > 0

    @property
    def has_discount(self):
        """Verifica si tiene descuento"""
        if self.compare_at_price:
            return self.price < self.compare_at_price
        return False

    # Calcula % de descuento
    @property
    def discount_percentage(self):
        if self.has_discount:
            discount = (self.compare_at_price - self.price) / self.compare_at_price
            return round(discount * 100)
        return 0

    # Deduce stock del inventario
    def deduct_stock(self, quantity):
        if self.product.track_inventory:
            if self.stock_quantity >= quantity:
                self.stock_quantity -= quantity
                self.save(update_fields=['stock_quantity', 'updated_at'])
                return True
            return False
        return True

    # Agrega stock al inventario"""
    def add_stock(self, quantity):
        if self.product.track_inventory:
            self.stock_quantity += quantity
            self.save(update_fields=['stock_quantity', 'updated_at'])