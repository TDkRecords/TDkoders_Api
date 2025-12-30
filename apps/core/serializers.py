from rest_framework import serializers
from .models import User, BusinessMember, Customer
from .models import BusinessType, Business, BusinessSettings
from .models import Category, Product, ProductVariant
from .models import Attribute, AttributeValue, ProductAttribute


# Serializer seguro para User - Solo lectura en vistas públicas
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "avatar",
            "user_type",
            "email_verified",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "user_type", "date_joined"]


class BusinessMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = BusinessMember
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CustomerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = [
            "id",
            "customer_number",
            "total_spent",
            "total_orders",
            "first_purchase_date",
            "last_purchase_date",
            "created_at",
            "updated_at",
        ]


class BusinessTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessType
        fields = "__all__"


class BusinessSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    is_subscription_active = serializers.ReadOnlyField()

    class Meta:
        model = Business
        exclude = ["stripe_account_id"]  # ← NO exponer datos sensibles
        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
            "subscription_status",
            "trial_ends_at",
        ]

    def get_member_count(self, obj):
        return obj.members.filter(is_active=True).count()


class BusinessSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSettings
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer para variantes con validación de atributos"""

    class Meta:
        model = ProductVariant
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_attributes(self, value):
        """Validar que los atributos existen y son válidos"""
        product = self.initial_data.get("product")
        if not product:
            raise serializers.ValidationError("Producto requerido")

        # Verificar que los atributos pertenezcan al producto
        product_attrs = ProductAttribute.objects.filter(product_id=product).values_list(
            "attribute__name", flat=True
        )

        for attr_name in value.keys():
            if attr_name not in product_attrs:
                raise serializers.ValidationError(
                    f"El atributo '{attr_name}' no pertenece a este producto"
                )

        return value


class ProductSerializer(serializers.ModelSerializer):
    """Serializer con variantes anidadas (opcional)"""

    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    price = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
            "price",
            "is_in_stock",
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear productos"""

    class Meta:
        model = Product
        fields = [
            "business",
            "category",
            "name",
            "description",
            "product_type",
            "is_service",
            "base_price",
            "track_inventory",
            "stock_quantity",
            "has_variants",
            "image_url",
            "is_active",
        ]

    def validate(self, data):
        # Si tiene variantes, stock_quantity no aplica
        if data.get("has_variants") and data.get("stock_quantity", 0) > 0:
            raise serializers.ValidationError(
                "Los productos con variantes no pueden tener stock_quantity. "
                "El stock se maneja por variante."
            )

        # Servicios no pueden tener inventario
        if data.get("is_service") and data.get("track_inventory"):
            raise serializers.ValidationError(
                "Los servicios no pueden tener control de inventario"
            )

        return data


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source="attribute.name", read_only=True)

    class Meta:
        model = AttributeValue
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)
    value_count = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_value_count(self, obj):
        return obj.values.filter(is_active=True).count()


class ProductAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttribute
        fields = "__all__"
