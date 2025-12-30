from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum

from .models import (
    Account,
    Transaction,
    TransactionEntry,
    Invoice,
    Expense,
    PaymentTerm,
)

from .serializers import (
    AccountSerializer,
    TransactionSerializer,
    TransactionEntrySerializer,
    InvoiceSerializer,
    ExpenseSerializer,
    PaymentTermSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Account.objects.filter(is_active=True)
        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)
        return qs

    @action(detail=True, methods=["get"])
    def entries(self, request, pk=None):
        """Ver movimientos de una cuenta"""
        account = self.get_object()
        entries = account.entries.select_related("transaction")
        serializer = TransactionEntrySerializer(entries, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.select_related(
            "business", "order", "created_by"
        ).prefetch_related("entries")
        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):
        """
        Contabilizar transacción:
        - Valida partida doble
        - Marca como posteada
        """
        transaction = self.get_object()

        if transaction.is_posted:
            return Response(
                {"detail": "La transacción ya está contabilizada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entries = transaction.entries.all()

        debit = (
            entries.filter(entry_type="debit").aggregate(total=Sum("amount"))["total"]
            or 0
        )
        credit = (
            entries.filter(entry_type="credit").aggregate(total=Sum("amount"))["total"]
            or 0
        )

        if debit != credit:
            return Response(
                {"detail": "La transacción no está balanceada"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction.is_posted = True
        transaction.posted_at = timezone.now()
        transaction.save(update_fields=["is_posted", "posted_at"])

        return Response({"detail": "Transacción contabilizada correctamente"})


class TransactionEntryViewSet(viewsets.ModelViewSet):
    queryset = TransactionEntry.objects.select_related("transaction", "account")
    serializer_class = TransactionEntrySerializer
    permission_classes = [permissions.IsAuthenticated]


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Invoice.objects.select_related("business", "customer", "order")
        business_id = self.request.query_params.get("business")
        status_param = self.request.query_params.get("status")

        if business_id:
            qs = qs.filter(business_id=business_id)
        if status_param:
            qs = qs.filter(status=status_param)

        return qs

    @action(detail=True, methods=["post"])
    def register_payment(self, request, pk=None):
        """Registrar un pago parcial o total"""
        invoice = self.get_object()
        amount = request.data.get("amount")

        if not amount:
            return Response(
                {"detail": "Monto requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.amount_paid += float(amount)
        invoice.paid_date = timezone.now().date()

        if invoice.amount_paid >= invoice.total:
            invoice.status = "paid"
        else:
            invoice.status = "partially_paid"

        invoice.save()
        return Response({"detail": "Pago registrado correctamente"})


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Expense.objects.select_related("business", "created_by", "approved_by")
        business_id = self.request.query_params.get("business")
        status_param = self.request.query_params.get("payment_status")

        if business_id:
            qs = qs.filter(business_id=business_id)
        if status_param:
            qs = qs.filter(payment_status=status_param)

        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        expense = self.get_object()
        expense.payment_status = "paid"
        expense.paid_date = timezone.now().date()
        expense.save(update_fields=["payment_status", "paid_date"])
        return Response({"detail": "Gasto marcado como pagado"})


class PaymentTermViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTermSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = PaymentTerm.objects.filter(is_active=True)
        business_id = self.request.query_params.get("business")
        if business_id:
            qs = qs.filter(business_id=business_id)
        return qs
