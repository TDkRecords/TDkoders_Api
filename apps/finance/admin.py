from django.contrib import admin
from .models import (
    Account,
    Transaction,
    TransactionEntry,
    Invoice,
    Expense,
    PaymentTerm,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "account_type", "balance", "is_active"]
    list_filter = ["account_type", "is_active", "business"]
    search_fields = ["code", "name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "transaction_number",
        "transaction_type",
        "transaction_date",
        "amount",
        "is_posted",
    ]
    list_filter = ["transaction_type", "is_posted", "business"]
    search_fields = ["transaction_number", "description"]


@admin.register(TransactionEntry)
class TransactionEntryAdmin(admin.ModelAdmin):
    list_display = ["transaction", "account", "entry_type", "amount"]
    list_filter = ["entry_type", "transaction__transaction_type"]
    search_fields = ["description"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "customer", "issue_date", "total", "status"]
    list_filter = ["status", "business"]
    search_fields = ["invoice_number", "customer__name"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "expense_number",
        "category",
        "expense_date",
        "amount",
        "payment_status",
    ]
    list_filter = ["category", "payment_status", "business"]
    search_fields = ["expense_number", "description"]


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ["name", "days", "discount_percentage", "is_active"]
    list_filter = ["is_active", "business"]
    search_fields = ["name"]


# Register your models here.
