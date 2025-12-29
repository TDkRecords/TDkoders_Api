from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.contrib import admin
from .models import (
    BusinessType,
    Business,
    BusinessSettings,
    User,
    BusinessMember,
    Customer,
    Category,
    Product,
    ProductVariant,
    Attribute,
    AttributeValue,
    ProductAttribute,
)


# BUSINESS MODELS
@admin.register(BusinessType)
class BusinessTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "has_inventory",
        "has_reservations",
        "has_services",
        "has_variants",
        "business_count",
    ]
    list_filter = ["has_inventory", "has_reservations", "has_services", "has_variants"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        ("Información Básica", {"fields": ("name", "slug", "description")}),
        (
            "Características",
            {
                "fields": (
                    "has_inventory",
                    "has_reservations",
                    "has_services",
                    "has_variants",
                    "default_attributes",
                )
            },
        ),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def business_count(self, obj):
        count = obj.businesses.count()
        return format_html("<b>{}</b> negocios", count)

    business_count.short_description = "Negocios"


class BusinessSettingsInline(admin.StackedInline):
    model = BusinessSettings
    can_delete = False
    verbose_name_plural = "Configuración"

    fieldsets = (
        ("Impuestos", {"fields": ("tax_name", "tax_rate", "tax_included_in_price")}),
        (
            "Métodos de Pago",
            {
                "fields": (
                    "accepts_online_payments",
                    "accepts_cash",
                    "accepts_card",
                    "requires_deposit",
                    "deposit_percentage",
                )
            },
        ),
        (
            "Reservas",
            {
                "fields": (
                    "min_booking_notice_hours",
                    "max_booking_days_advance",
                    "cancellation_policy",
                )
            },
        ),
        ("Inventario", {"fields": ("low_stock_threshold", "auto_detect_inventory")}),
        (
            "Notificaciones",
            {
                "fields": (
                    "send_order_confirmation",
                    "send_reservation_confirmation",
                    "reminder_hours_before",
                )
            },
        ),
        ("Horarios", {"fields": ("bussines_hours",)}),
    )


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "business_type",
        "city",
        "country",
        "subscription_badge",
        "is_verified",
        "is_active",
        "member_count",
        "product_count",
    ]
    list_filter = [
        "business_type",
        "subscription_status",
        "is_active",
        "is_verified",
        "country",
        "created_at",
    ]
    search_fields = ["name", "slug", "email", "phone", "city"]
    readonly_fields = ["id", "slug", "created_at", "updated_at", "subscription_info"]
    date_hierarchy = "created_at"

    inlines = [BusinessSettingsInline]

    fieldsets = (
        ("Información Básica", {"fields": ("name", "slug", "business_type", "logo")}),
        ("Contacto", {"fields": ("email", "phone", "website")}),
        (
            "Ubicación",
            {"fields": ("address", "city", "state", "country", "postal_code")},
        ),
        ("Configuración Regional", {"fields": ("timezone", "currency")}),
        (
            "Stripe",
            {
                "fields": ("stripe_account_id", "stripe_onboarding_complete"),
                "classes": ("collapse",),
            },
        ),
        (
            "Suscripción y Estado",
            {
                "fields": (
                    "subscription_status",
                    "trial_ends_at",
                    "is_active",
                    "is_verified",
                    "subscription_info",
                )
            },
        ),
        (
            "Soft Delete",
            {"fields": ("is_deleted", "deleted_at"), "classes": ("collapse",)},
        ),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def subscription_badge(self, obj):
        colors = {
            "trial": "#FFA500",
            "active": "#28a745",
            "past_due": "#dc3545",
            "cancelled": "#6c757d",
        }
        color = colors.get(obj.subscription_status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_subscription_status_display(),
        )

    subscription_badge.short_description = "Suscripción"

    def subscription_info(self, obj):
        info = f"Estado: {obj.get_subscription_status_display()}<br>"
        if obj.trial_ends_at:
            info += f"Trial termina: {obj.trial_ends_at.strftime('%Y-%m-%d %H:%M')}<br>"
        info += f"Activo: {'✓' if obj.is_subscription_active else '✗'}"
        return mark_safe(info)

    subscription_info.short_description = "Info de Suscripción"

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "Miembros"

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Productos"


# USER MODELS}
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "full_name",
        "user_type_badge",
        "email_verified",
        "phone_verified",
        "is_active",
        "date_joined",
    ]
    list_filter = [
        "user_type",
        "is_active",
        "is_staff",
        "email_verified",
        "phone_verified",
        "date_joined",
    ]
    search_fields = ["email", "first_name", "last_name", "phone"]
    readonly_fields = ["id", "date_joined", "last_login", "created_at", "updated_at"]
    date_hierarchy = "date_joined"

    fieldsets = (
        ("Autenticación", {"fields": ("email", "password")}),
        (
            "Información Personal",
            {"fields": ("first_name", "last_name", "phone", "avatar")},
        ),
        (
            "Permisos",
            {
                "fields": (
                    "user_type",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Verificación", {"fields": ("email_verified", "phone_verified")}),
        (
            "Fechas Importantes",
            {
                "fields": ("date_joined", "last_login", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
        ("Metadatos", {"fields": ("id",), "classes": ("collapse",)}),
    )

    def user_type_badge(self, obj):
        colors = {
            "business_owner": "#007bff",
            "employee": "#28a745",
            "customer": "#6c757d",
            "admin": "#dc3545",
        }
        color = colors.get(obj.user_type, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_user_type_display(),
        )

    user_type_badge.short_description = "Tipo"


@admin.register(BusinessMember)
class BusinessMemberAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "business",
        "role_badge",
        "is_active",
        "invited_by",
        "invitation_accepted_at",
    ]
    list_filter = ["role", "is_active", "business", "created_at"]
    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "business__name",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["user", "business", "invited_by"]

    fieldsets = (
        ("Relación", {"fields": ("user", "business", "role")}),
        ("Permisos", {"fields": ("permissions", "is_active")}),
        ("Invitación", {"fields": ("invited_by", "invitation_accepted_at")}),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def role_badge(self, obj):
        colors = {
            "owner": "#dc3545",
            "admin": "#fd7e14",
            "manager": "#007bff",
            "employee": "#28a745",
            "cashier": "#6c757d",
        }
        color = colors.get(obj.role, "#6c757d")
        return mark_safe(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_role_display(),
        )

    role_badge.short_description = "Rol"


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "customer_number",
        "user",
        "business",
        "total_spent",
        "total_orders",
        "loyalty_points",
        "is_vip",
        "is_blocked",
    ]
    list_filter = [
        "business",
        "is_vip",
        "is_blocked",
        "prefer_email",
        "prefer_sms",
        "created_at",
    ]
    search_fields = [
        "customer_number",
        "user__email",
        "user__first_name",
        "user__last_name",
        "notes",
    ]
    readonly_fields = [
        "id",
        "customer_number",
        "created_at",
        "updated_at",
        "customer_stats",
    ]
    date_hierarchy = "created_at"
    autocomplete_fields = ["user", "business"]

    fieldsets = (
        ("Información Básica", {"fields": ("customer_number", "user", "business")}),
        (
            "Estadísticas",
            {
                "fields": (
                    "total_spent",
                    "total_orders",
                    "loyalty_points",
                    "customer_stats",
                )
            },
        ),
        ("Estados", {"fields": ("is_vip", "is_blocked")}),
        ("Preferencias de Contacto", {"fields": ("prefer_email", "prefer_sms")}),
        ("Notas", {"fields": ("notes",)}),
        (
            "Fechas Importantes",
            {
                "fields": ("first_purchase_date", "last_purchase_date"),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def customer_stats(self, obj):
        stats = f"<b>Total gastado:</b> ${obj.total_spent}<br>"
        stats += f"<b>Total órdenes:</b> {obj.total_orders}<br>"
        stats += f"<b>Puntos:</b> {obj.loyalty_points}<br>"
        if obj.first_purchase_date:
            stats += f"<b>Primera compra:</b> {obj.first_purchase_date.strftime('%Y-%m-%d')}<br>"
        if obj.last_purchase_date:
            stats += (
                f"<b>Última compra:</b> {obj.last_purchase_date.strftime('%Y-%m-%d')}"
            )
        return mark_safe(stats)

    customer_stats.short_description = "Estadísticas"


# PRODUCT MODELS
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "business", "parent", "order", "is_active", "product_count"]
    list_filter = ["business", "is_active", "parent"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["business", "parent"]

    fieldsets = (
        ("Información Básica", {"fields": ("business", "name", "slug", "description")}),
        ("Jerarquía", {"fields": ("parent", "order")}),
        ("Estado", {"fields": ("is_active",)}),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Productos"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ["name", "sku", "price", "stock_quantity", "is_active", "is_default"]
    readonly_fields = ["id"]


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 0
    fields = ["attribute", "is_required", "order"]
    autocomplete_fields = ["attribute"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "business",
        "category",
        "product_type",
        "base_price",
        "stock_status",
        "has_variants",
        "is_active",
        "is_featured",
    ]
    list_filter = [
        "business",
        "category",
        "product_type",
        "is_service",
        "has_variants",
        "is_active",
        "is_featured",
        "track_inventory",
    ]
    search_fields = ["name", "sku", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "product_info"]
    date_hierarchy = "created_at"
    autocomplete_fields = ["business", "category"]

    inlines = [ProductAttributeInline, ProductVariantInline]

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("business", "category", "name", "description", "sku")},
        ),
        (
            "Tipo de Producto",
            {"fields": ("product_type", "is_service", "service_duration_minutes")},
        ),
        (
            "Precio e Inventario",
            {"fields": ("base_price", "track_inventory", "stock_quantity")},
        ),
        ("Imágenes", {"fields": ("image_url", "images")}),
        ("Variantes", {"fields": ("has_variants",)}),
        ("Estado", {"fields": ("is_active", "is_featured")}),
        (
            "SEO",
            {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)},
        ),
        ("Info del Producto", {"fields": ("product_info",)}),
        (
            "Soft Delete",
            {"fields": ("is_deleted", "deleted_at"), "classes": ("collapse",)},
        ),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def stock_status(self, obj):
        if not obj.track_inventory:
            return mark_safe('<span style="color: #6c757d;">Sin seguimiento</span>')

        if obj.is_in_stock:
            color = "#28a745" if obj.stock_quantity > 10 else "#FFA500"
            return mark_safe(
                '<span style="color: {};">{} unidades</span>', color, obj.stock_quantity
            )
        return mark_safe('<span style="color: #dc3545;">Sin stock</span>')

    stock_status.short_description = "Stock"

    def product_info(self, obj):
        info = f"<b>Precio:</b> ${obj.price}<br>"
        info += f"<b>En stock:</b> {'✓' if obj.is_in_stock else '✗'}<br>"
        if obj.has_variants:
            variant_count = obj.variants.count()
            info += f"<b>Variantes:</b> {variant_count}<br>"
        return mark_safe(info)

    product_info.short_description = "Información"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "product",
        "sku",
        "price",
        "stock_quantity",
        "discount_info",
        "is_active",
        "is_default",
    ]
    list_filter = ["product__business", "is_active", "is_default", "product"]
    search_fields = ["name", "sku", "product__name"]
    readonly_fields = ["id", "created_at", "updated_at", "variant_info"]
    autocomplete_fields = ["product"]

    fieldsets = (
        ("Información Básica", {"fields": ("product", "name", "sku", "attributes")}),
        ("Precios", {"fields": ("price", "compare_at_price", "cost_price")}),
        ("Inventario", {"fields": ("stock_quantity",)}),
        ("Imagen", {"fields": ("image_url",)}),
        ("Estado", {"fields": ("is_active", "is_default", "order")}),
        ("Info de Variante", {"fields": ("variant_info",)}),
        (
            "Soft Delete",
            {"fields": ("is_deleted", "deleted_at"), "classes": ("collapse",)},
        ),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def discount_info(self, obj):
        if obj.has_discount:
            return mark_safe(
                '<span style="color: #dc3545;">-{}%</span>', obj.discount_percentage
            )
        return "-"

    discount_info.short_description = "Descuento"

    def variant_info(self, obj):
        info = f"<b>Precio:</b> ${obj.price}<br>"
        if obj.compare_at_price:
            info += f"<b>Precio anterior:</b> ${obj.compare_at_price}<br>"
            info += f"<b>Descuento:</b> {obj.discount_percentage}%<br>"
        if obj.cost_price:
            margin = obj.price - obj.cost_price
            margin_pct = (margin / obj.price * 100) if obj.price > 0 else 0
            info += f"<b>Margen:</b> ${margin} ({margin_pct:.1f}%)<br>"
        info += f"<b>En stock:</b> {'✓' if obj.is_in_stock else '✗'}"
        return mark_safe(info)

    variant_info.short_description = "Información"


# ATTRIBUTE MODELS
class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ["value", "color_code", "order", "is_active"]


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "business",
        "attribute_type",
        "unit",
        "is_required",
        "is_variant_attribute",
        "is_active",
        "value_count",
    ]
    list_filter = [
        "business",
        "attribute_type",
        "is_required",
        "is_variant_attribute",
        "is_active",
    ]
    search_fields = ["name", "unit"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["business"]

    inlines = [AttributeValueInline]

    fieldsets = (
        (
            "Información Básica",
            {"fields": ("business", "name", "attribute_type", "unit")},
        ),
        ("Configuración", {"fields": ("is_required", "is_variant_attribute", "order")}),
        ("Estado", {"fields": ("is_active",)}),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def value_count(self, obj):
        return obj.values.count()

    value_count.short_description = "Valores"


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ["value", "attribute", "color_preview", "order", "is_active"]
    list_filter = ["attribute__business", "attribute", "is_active"]
    search_fields = ["value", "attribute__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["attribute"]

    fieldsets = (
        ("Información Básica", {"fields": ("attribute", "value", "color_code")}),
        ("Configuración", {"fields": ("order", "is_active")}),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def color_preview(self, obj):
        if obj.color_code:
            return mark_safe(
                '<div style="width: 50px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.color_code,
            )
        return "-"

    color_preview.short_description = "Color"


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ["product", "attribute", "is_required", "order"]
    list_filter = ["product__business", "is_required"]
    search_fields = ["product__name", "attribute__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    autocomplete_fields = ["product", "attribute"]

    fieldsets = (
        ("Relación", {"fields": ("product", "attribute")}),
        ("Configuración", {"fields": ("is_required", "order")}),
        (
            "Metadatos",
            {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# CUSTOMIZACIÓN DEL ADMIN SITE}
admin.site.site_header = "TDkoders Administration"
admin.site.site_title = "TDkoders Admin"
admin.site.index_title = "Panel de Administración"
