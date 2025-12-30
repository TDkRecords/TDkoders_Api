from rest_framework import serializers
from .models import (
    Account,
    Transaction,
    TransactionEntry,
    Invoice,
    Expense,
    PaymentTerm,
)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"


class TransactionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionEntry
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    entries = TransactionEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = "__all__"
        extra_kwargs = {
            "transaction_number": {"read_only": True},
            "created_by": {"read_only": True},
            "posted_at": {"read_only": True},
            "is_posted": {"read_only": True},
        }


class InvoiceSerializer(serializers.ModelSerializer):
    balance_due = serializers.ReadOnlyField()
    is_paid = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = "__all__"
        extra_kwargs = {
            "invoice_number": {"read_only": True},
        }


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"
        extra_kwargs = {
            "expense_number": {"read_only": True},
            "total": {"read_only": True},
            "created_by": {"read_only": True},
        }


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = "__all__"
