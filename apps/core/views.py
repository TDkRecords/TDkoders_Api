from rest_framework import viewsets
from .permissions import IsBusinessMemberOrReadOnly, BusinessFilterMixin
from .serializers import (
    UserSerializer,
    BusinessMemberSerializer,
    CustomerSerializer,
    BusinessTypeSerializer,
    BusinessSerializer,
    BusinessSettingsSerializer,
    CategorySerializer,
    ProductSerializer,
    ProductVariantSerializer,
    AttributeSerializer,
    AttributeValueSerializer,
    ProductAttributeSerializer,
)

from .models import (
    User,
    BusinessMember,
    Customer,
    BusinessType,
    Business,
    BusinessSettings,
    Category,
    Product,
    ProductVariant,
    Attribute,
    AttributeValue,
    ProductAttribute,
)


# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()


class BusinessMemberViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessMemberSerializer
    queryset = BusinessMember.objects.all()


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()


class BusinessTypeViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessTypeSerializer
    queryset = BusinessType.objects.all()


class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    queryset = Business.objects.all()


class BusinessSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSettingsSerializer
    queryset = BusinessSettings.objects.all()


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


class ProductViewSet(BusinessFilterMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsBusinessMemberOrReadOnly]

    def perform_create(self, serializer):
        # Verificar que el usuario tenga permiso en este business
        business_id = self.request.data.get("business")
        from apps.core.models import BusinessMember

        if not BusinessMember.objects.filter(
            business_id=business_id,
            user=self.request.user,
            is_active=True,
            role__in=["owner", "admin", "manager"],
        ).exists():
            raise PermissionDenied(
                "No tienes permiso para crear productos en este negocio"
            )

        serializer.save()


class ProductVariantViewSet(viewsets.ModelViewSet):
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.all()


class AttributeViewSet(viewsets.ModelViewSet):
    serializer_class = AttributeSerializer
    queryset = Attribute.objects.all()


class AttributeValueViewSet(viewsets.ModelViewSet):
    serializer_class = AttributeValueSerializer
    queryset = AttributeValue.objects.all()


class ProductAttributeViewSet(viewsets.ModelViewSet):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.all()
