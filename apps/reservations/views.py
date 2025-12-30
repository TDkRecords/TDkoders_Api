from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

from .models import (
    ServiceProvider,
    Reservation,
    ReservationService,
    ReservationStatusHistory,
    ServiceProviderAvailability,
    WaitingList,
)
from .serializers import (
    ServiceProviderSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    ReservationDetailSerializer,
    ReservationCreateSerializer,
    ReservationServiceSerializer,
    ReservationStatusHistorySerializer,
    ServiceProviderAvailabilitySerializer,
    WaitingListSerializer,
)


class ServiceProviderViewSet(viewsets.ModelViewSet):
    queryset = ServiceProvider.objects.select_related("business", "user")
    serializer_class = ServiceProviderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)
        return qs


class ReservationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.select_related(
            "business", "customer", "service_provider"
        ).prefetch_related(
            "services",
            "status_history",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        if self.action == "retrieve":
            return ReservationDetailSerializer
        if self.action == "create":
            return ReservationCreateSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        reservation = self.get_object()
        new_status = request.data.get("status")
        notes = request.data.get("notes", "")

        if new_status not in dict(Reservation.STATUS_CHOICES):
            return Response(
                {"detail": "Estado inválido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = reservation.status
        reservation.status = new_status
        reservation.save(update_fields=["status", "updated_at"])

        ReservationStatusHistory.objects.create(
            reservation=reservation,
            previous_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            notes=notes,
        )

        return Response(
            {"detail": "Estado actualizado correctamente"},
            status=status.HTTP_200_OK,
        )


class ReservationServiceViewSet(viewsets.ModelViewSet):
    queryset = ReservationService.objects.select_related("reservation", "product")
    serializer_class = ReservationServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.reservation.calculate_total()


class ServiceProviderAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = ServiceProviderAvailability.objects.select_related("service_provider")
    serializer_class = ServiceProviderAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        provider_id = self.request.query_params.get("service_provider")
        if provider_id:
            qs = qs.filter(service_provider_id=provider_id)
        return qs


class WaitingListViewSet(viewsets.ModelViewSet):
    queryset = WaitingList.objects.select_related(
        "business", "customer", "service_provider"
    )
    serializer_class = WaitingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)
        return qs
