from django.urls import path, include

from .views import *
from .tests import *

app_name = "finance"

urlpatterns = [
    path('add_bank_activity/', AddBankActivityView.as_view(), name="add_bank_activity"),
    path('finance_summary/', FinanceSummaryView.as_view(), name="finance_summary"),
    path('add_finmaks_transaction/', AddFinmaksTransactionView.as_view(), name="add_finmaks_transaction"),
    path('update_finmaks_transaction_name/', UpdateFinmaksTransactionNameView.as_view(), name="update_finmaks_transaction_name"),
    path('bank_account_balances/', BankAccountBalancesView.as_view(), name="bank_account_balances"),

    path('', include("finance.api.urls")),
]