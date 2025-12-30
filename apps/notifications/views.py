from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.select_related("business", "recipient")
        if not self.request.user.is_superuser:
            qs = qs.filter(recipient=self.request.user)

        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)

        is_read = self.request.query_params.get("is_read")
        if is_read in {"true", "false"}:
            qs = qs.filter(is_read=(is_read == "true"))

        ntype = self.request.query_params.get("type")
        if ntype:
            qs = qs.filter(notification_type=ntype)

        return qs

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_read()
        return Response({"detail": "Notificación marcada como leída"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(is_read=False)
        updated = 0
        from django.utils import timezone

        updated = qs.update(is_read=True, read_at=timezone.now())
        return Response({"detail": f"{updated} notificaciones marcadas como leídas"})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = NotificationPreference.objects.select_related("business", "user").filter(
            user=self.request.user
        )
        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
