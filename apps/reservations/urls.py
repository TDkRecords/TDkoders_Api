from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

router = DefaultRouter()
router.register(r"reservations", views.ReservationViewSet, basename="reservation")
router.register(
    r"reservation-services",
    views.ReservationServiceViewSet,
    basename="reservation-service",
)
router.register(
    r"service-providers", views.ServiceProviderViewSet, basename="service-provider"
)
router.register(
    r"service-provider-availabilities",
    views.ServiceProviderAvailabilityViewSet,
    basename="service-provider-availability",
)
router.register(r"waiting-list", views.WaitingListViewSet, basename="waiting-list")

urlpatterns = [
    path("", include(router.urls)),
]
