# apps/core/models/attribute.py
from django.db import models
from .base import TimeStampedModel, UUIDModel
from .business import Business


class Attribute(TimeStampedModel, UUIDModel):
    """
    Define los atributos que pueden tener los productos.
    
    ¿Qué es un atributo?
    Una CARACTERÍSTICA que define variantes:
    - Tienda de ropa: "Talla", "Color", "Material"
    - Supermercado: "Peso", "Marca", "Presentación"
    - Barbería: "Duración", "Barbero"
    
    ¿Por qué es importante?
    Cada negocio puede definir SUS PROPIOS atributos.
    Tu sistema es FLEXIBLE y se adapta a cualquier negocio.
    
    CAMBIOS: Tú lo tenías vacío con pass, yo lo llené completamente.
    """
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='attributes'
    )
    
    # ---- Nombre del atributo ----
    name = models.CharField(
        max_length=100,
        help_text="Nombre del atributo (ej: Talla, Color, Peso)"
    )
    
    # ---- Tipo de dato ----
    ATTRIBUTE_TYPE_CHOICES = [
        ('text', 'Text'),           # Texto libre
        ('number', 'Number'),       # Número
        ('select', 'Select'),       # Lista de opciones (el más común)
        ('color', 'Color'),         # Selector de color
        ('boolean', 'Yes/No'),      # Sí/No
    ]
    attribute_type = models.CharField(
        max_length=20,
        choices=ATTRIBUTE_TYPE_CHOICES,
        default='select'
    )
    
    # ---- Unidad de medida ----
    unit = models.CharField(
        max_length=20,
        blank=True,
        help_text="Unidad de medida (ej: kg, ml, cm, min)"
    )
    
    # ---- ¿Es obligatorio? ----
    is_required = models.BooleanField(
        default=False,
        help_text="¿Este atributo es obligatorio para crear variantes?"
    )
    
    # ---- ¿Se usa para variantes? ----
    is_variant_attribute = models.BooleanField(
        default=True,
        help_text="¿Este atributo define variantes?"
    )
    
    # ---- Estado ----
    is_active = models.BooleanField(default=True)
    
    # ---- Orden ----
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'attributes'
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'
        unique_together = [['business', 'name']]
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['business', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.business.name})"


class AttributeValue(TimeStampedModel, UUIDModel):
    """
    Valores predefinidos para un atributo tipo 'select'.
    
    ¿Para qué?
    Si el atributo es "Talla", los valores son: "S", "M", "L", "XL"
    Si el atributo es "Color", los valores son: "Rojo", "Azul", "Verde"
    
    Ejemplo de flujo:
    1. Crear atributo: name="Talla", type="select"
    2. Crear valores: "S", "M", "L", "XL"
    3. Usar en variante: attributes={"Talla": "M"}
    
    CAMBIOS: Tú lo tenías vacío con pass, yo lo llené completamente.
    """
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='values'
    )
    
    # ---- Valor ----
    value = models.CharField(
        max_length=100,
        help_text="Valor del atributo (ej: M, Rojo, 500g)"
    )
    
    # ---- Código de color (solo para colores) ----
    color_code = models.CharField(
        max_length=7,
        blank=True,
        help_text="Código hexadecimal del color (ej: #FF0000)"
    )
    
    # ---- Estado ----
    is_active = models.BooleanField(default=True)
    
    # ---- Orden ----
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'attribute_values'
        verbose_name = 'Valor de Atributo'
        verbose_name_plural = 'Valores de Atributos'
        unique_together = [['attribute', 'value']]
        ordering = ['order', 'value']
        indexes = [
            models.Index(fields=['attribute', 'is_active']),
        ]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductAttribute(TimeStampedModel, UUIDModel):
    """
    Relación entre un producto y sus atributos.
    
    ¿Para qué?
    Define QUÉ atributos tiene un producto específico.
    
    Ejemplo:
    - Producto "Camisa" tiene atributos: Talla, Color
    - Producto "Arroz" tiene atributos: Peso, Marca
    
    Entonces cuando creas variantes, sabes qué atributos usar.
    
    CAMBIOS: Tú lo tenías vacío con pass, yo lo llené completamente.
    """
    # ⚠️ IMPORTANTE: Importación circular
    # Como Product está en otro archivo, lo importamos aquí
    from .product import Product
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_attributes'
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='product_attributes'
    )
    
    # ---- ¿Es obligatorio? ----
    is_required = models.BooleanField(default=False)
    
    # ---- Orden ----
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'product_attributes'
        verbose_name = 'Atributo de Producto'
        verbose_name_plural = 'Atributos de Productos'
        unique_together = [['product', 'attribute']]
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}"