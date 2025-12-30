from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Payment, PaymentWebhookEvent
from .serializers import PaymentSerializer, PaymentWebhookEventSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Payment.objects.select_related(
            "business", "invoice", "order", "created_by"
        )

        business_id = self.request.query_params.get("business")
        status_param = self.request.query_params.get("status")
        provider = self.request.query_params.get("provider")

        if business_id:
            qs = qs.filter(business_id=business_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if provider:
            qs = qs.filter(provider=provider)

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_captured(self, request, pk=None):
        payment = self.get_object()

        if payment.status not in {"pending", "authorized"}:
            return Response(
                {"detail": "Estado inválido para capturar"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.status = "captured"
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "paid_at", "updated_at"])

        invoice = payment.invoice
        if invoice:
            invoice.amount_paid += payment.amount
            if invoice.amount_paid >= invoice.total:
                invoice.status = "paid"
                invoice.paid_date = timezone.now().date()
            else:
                invoice.status = "partially_paid"
            invoice.save()

        return Response({"detail": "Pago marcado como capturado"})

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        payment = self.get_object()
        amount = request.data.get("amount")

        if payment.status != "captured":
            return Response(
                {"detail": "Solo pagos capturados pueden ser reembolsados"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            amount = float(amount) if amount is not None else float(payment.amount)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Monto inválido"}, status=status.HTTP_400_BAD_REQUEST
            )

        if amount <= 0 or amount > float(payment.amount):
            return Response(
                {"detail": "Monto fuera de rango"}, status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = "refunded"
        payment.refunded_amount = amount
        payment.save(update_fields=["status", "refunded_amount", "updated_at"])

        invoice = payment.invoice
        if invoice:
            invoice.amount_paid = max(0, float(invoice.amount_paid) - amount)
            if invoice.amount_paid <= 0:
                invoice.status = "sent"
                invoice.paid_date = None
            else:
                invoice.status = "partially_paid"
            invoice.save()

        return Response({"detail": "Reembolso registrado"})


class PaymentWebhookEventViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentWebhookEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = PaymentWebhookEvent.objects.select_related("business")
        business_id = self.request.query_params.get("business")
        provider = self.request.query_params.get("provider")

        if business_id:
            qs = qs.filter(business_id=business_id)
        if provider:
            qs = qs.filter(provider=provider)
        return qs


# Create your views here.
