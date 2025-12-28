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
admin.site.register(BusinessType)
admin.site.register(Business)
admin.site.register(BusinessSettings)

# USER MODELS
admin.site.register(User)
admin.site.register(BusinessMember)
admin.site.register(Customer)

# PRODUCT MODELS
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductVariant)

# ATTRIBUTE MODELS
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(ProductAttribute)