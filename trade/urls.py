from django.urls import path, include

from .views import *
from .tests import *

app_name = "trade"

urlpatterns = [
    path('export_trade_transactions_for_customer/', ExportTradeTransactionsForCustomerView.as_view(), name="export_trade_transactions_for_customer"),
    path('trade_transactions_for_customer_excel/', TradeTransactionsForCustomerExcelView.as_view(), name="trade_transactions_for_customer_excel"),
    path('', include("trade.api.urls")),
]