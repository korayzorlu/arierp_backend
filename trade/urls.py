from django.urls import path, include

from .views import *
from .tests import *

app_name = "trade"

urlpatterns = [
    path('export_trade_transactions_for_customers/', ExportTradeTransactionForCustomersView.as_view(), name="export_trade_transactions_for_customers"),
    path('trade_transactions_for_customers_excel/', TradeTransactionForCustomersExcelView.as_view(), name="trade_transactions_for_customers_excel"),
    path('', include("trade.api.urls")),
]