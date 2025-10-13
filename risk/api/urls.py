from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'amount_debit_transactions',AmountDebitTransactionList, "amount_debit_transactions_api")
router.register(r'under_reviews', UnderReviewList, "under_reviews_api")

urlpatterns = [
    path('',include(router.urls)),
]
