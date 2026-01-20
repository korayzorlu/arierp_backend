from django.urls import path, include
from rest_framework import routers

from .views.accounts_views import *
from .views.trial_balances_views import *
from .views.trial_balance_transactions_views import *
from .views.bddk_views import *

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
router.register(r'bddk_hesaplar', BDDKHesaplarList, "bddk_hesaplar_api")
router.register(r'bl222af', Bl222afList, "bl222af_api")
router.register(r'kz222af', Kz222afList, "kz222af_api")

urlpatterns = [
    path('',include(router.urls)),
]
