from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'accounts', AccountList, "accounts_api")
router.register(r'transactions', TransactionList, "transactions_api")
router.register(r'invoices', InvoiceList, "invoices_api")
router.register(r'payments', PaymentList, "payments_api")
router.register(r'main_account_codes', MainAccountCodeList, "main_account_codes_api")
router.register(r'trial_balances', TrialBalanceList, "trial_balances_api")
router.register(r'trial_balance_contracts', TrialBalanceContractList, "trial_balance_contracts_api")
router.register(r'trial_balance_transactions', TrialBalanceTransactionList, "trial_balance_transactions_api")
router.register(r'under_reviews', UnderReviewList, "under_reviews_api")

urlpatterns = [
    path('',include(router.urls)),
]
