from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"business-members", views.BusinessMemberViewSet)
router.register(r"customers", views.CustomerViewSet)
router.register(r"business-types", views.BusinessTypeViewSet)
router.register(r"businesses", views.BusinessViewSet)
router.register(r"business-settings", views.BusinessSettingsViewSet)
router.register(r"categories", views.CategoryViewSet)
router.register(r"products", views.ProductViewSet)
router.register(r"variants", views.ProductVariantViewSet)
router.register(r"attributes", views.AttributeViewSet)
router.register(r"attribute-values", views.AttributeValueViewSet)
router.register(r"product-attributes", views.ProductAttributeViewSet)

urlpatterns = [
    path("core/", include(router.urls)),
]
