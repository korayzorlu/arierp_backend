from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'accounts', AccountList, "accounts_api")
router.register(r'transactions', TransactionList, "transactions_api")
router.register(r'invoices', InvoiceList, "invoices_api")
router.register(r'payments', PaymentList, "payments_api")

urlpatterns = [
    path('',include(router.urls)),
]
