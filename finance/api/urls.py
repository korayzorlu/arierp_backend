from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'bank_accounts', BankAccountList, "bank_accounts_api")
router.register(r'bank_account_transactions', BankAccountTransactionList, "bank_account_transactions_api")

urlpatterns = [
    path('',include(router.urls)),
]
