from django.urls import path, include

from .views import *
from .tests import *

app_name = "risk"

urlpatterns = [
    path('export_amount_debit_transactions/', ExportAmountDebitTransactionsView.as_view(), name="export_amount_debit_transactions"),
    path('amount_debit_transactions_excel/', AmountDebitTransactionsExcelView.as_view(), name="amount_debit_transactions_excel"),
    
    path('', include("risk.api.urls")),
]