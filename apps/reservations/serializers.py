from rest_framework import serializers
from .models import (
    ServiceProvider,
    Reservation,
    ReservationService,
    ReservationStatusHistory,
    ServiceProviderAvailability,
    WaitingList,
)


class ServiceProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProvider
        fields = "__all__"


class ReservationServiceSerializer(serializers.ModelSerializer):
    product_name = serializers.StringRelatedField(source="product", read_only=True)

    class Meta:
        model = ReservationService
        fields = "__all__"


class ReservationStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.StringRelatedField(
        source="changed_by", read_only=True
    )

    class Meta:
        model = ReservationStatusHistory
        fields = "__all__"


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = "__all__"


class ReservationListSerializer(ReservationSerializer):
    service_provider_name = serializers.StringRelatedField(
        source="service_provider", read_only=True
    )
    customer_name_display = serializers.SerializerMethodField()

    def get_customer_name_display(self, obj):
        if obj.customer:
            return obj.customer.user.full_name
        return obj.customer_name


class ReservationDetailSerializer(ReservationSerializer):
    services = ReservationServiceSerializer(many=True, read_only=True)
    status_history = ReservationStatusHistorySerializer(many=True, read_only=True)
    service_provider = ServiceProviderSerializer(read_only=True)


class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "business",
            "customer",
            "customer_name",
            "customer_email",
            "customer_phone",
            "service_provider",
            "start_datetime",
            "end_datetime",
            "notes",
            "customer_notes",
            "requires_deposit",
            "deposit_amount",
        ]

    def validate(self, data):
        if data["end_datetime"] <= data["start_datetime"]:
            raise serializers.ValidationError(
                "La hora de fin debe ser posterior a la de inicio"
            )
        return data


class ServiceProviderAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProviderAvailability
        fields = "__all__"


class WaitingListSerializer(serializers.ModelSerializer):
    customer_name = serializers.StringRelatedField(source="customer", read_only=True)
    service_provider_name = serializers.StringRelatedField(
        source="service_provider", read_only=True
    )

    class Meta:
        model = WaitingList
        fields = "__all__"
