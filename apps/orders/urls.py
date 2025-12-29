from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()

router.register(r"orders", views.OrderViewSet, basename="order")
router.register(r"order-items", views.OrderItemViewSet, basename="order-item")

urlpatterns = [
    path("", include(router.urls)),
]
