from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r"accounts", views.AccountViewSet, basename="account")
router.register(r"transactions", views.TransactionViewSet, basename="transaction")
router.register(
    r"transaction-entries", views.TransactionEntryViewSet, basename="transaction-entry"
)
router.register(r"invoices", views.InvoiceViewSet, basename="invoice")
router.register(r"expenses", views.ExpenseViewSet, basename="expense")
router.register(r"payment-terms", views.PaymentTermViewSet, basename="payment-term")


urlpatterns = [
    path("", include(router.urls)),
]
