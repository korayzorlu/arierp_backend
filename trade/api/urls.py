from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'trade_accounts',TradeAccountList, "trade_accounts_api")
router.register(r'trade_transactions',TradeTransactionList, "trade_transactions_api")
router.register(r'trade_transactions_for_lease',TradeTransactionForLeaseList, "trade_transactions_for_lease_api")
router.register(r'trade_transactions_for_customer_in_lease',TradeTransactionForCustomerInLeaseList, "trade_transactions_for_customer_in_lease_api")

urlpatterns = [
    path('',include(router.urls)),
]
