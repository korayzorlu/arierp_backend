from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from .views.finmaks_views import *
from .views.vpos_views import *
from .tests import *

app_name = "finance"

urlpatterns = [
    path('add_bank_activity/', AddBankActivityView.as_view(), name="add_bank_activity"),
    path('finance_summary/', FinanceSummaryView.as_view(), name="finance_summary"),
    path('add_finmaks_transaction/', AddFinmaksTransactionView.as_view(), name="add_finmaks_transaction"),
    path('update_finmaks_transaction_name/', UpdateFinmaksTransactionNameView.as_view(), name="update_finmaks_transaction_name"),
    path('export_finmaks_bank_account_balances/', ExportFinmaksBankAccountBalancesView.as_view(), name="export_finmaks_bank_account_balances"),
    path('finmaks_bank_account_balances_excel/', FinmaksBankAccountBalancesExcelView.as_view(), name="finmaks_bank_account_balances_excel"),
    path('add_vpos_transaction/', csrf_exempt(AddVPosTransactionView.as_view()), name="add_vpos_transaction"),

    path('', include("finance.api.urls")),
]