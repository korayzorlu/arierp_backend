from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'bank_accounts', BankAccountList, "bank_accounts_api")
router.register(r'bank_account_balances', BankAccountBalanceList, "bank_account_balances_api")
router.register(r'bank_account_daily_records', BankAccountDailyRecordList, "bank_account_daily_records_api")
router.register(r'bank_account_transactions', BankAccountTransactionList, "bank_account_transactions_api")
router.register(r'partner_advances', PartnerAdvanceList, "partner_advances_api")

urlpatterns = [
    path('',include(router.urls)),
]
