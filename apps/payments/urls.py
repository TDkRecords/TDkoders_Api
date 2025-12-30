from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r"payments", views.PaymentViewSet, basename="payment")
router.register(
    r"webhook-events",
    views.PaymentWebhookEventViewSet,
    basename="payment-webhook-event",
)

urlpatterns = [
    path("", include(router.urls)),
]
