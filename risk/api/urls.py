from django.urls import path, include
from rest_framework import routers

from risk.api.views.to_be_transferred_views import ToBeTransferredList
from risk.api.views.to_terminated_risk_partners_views import ToTerminatedRiskPartnerList
from risk.api.views.warned_risk_partners_views import WarnedRiskPartnerList
from risk.api.views.risk_partners_views import RiskPartnerList
from risk.api.views.to_warned_risk_partnes_views import ToWarnedRiskPartnerList
from risk.api.views.today_partners_views import TodayPartnerList
from risk.api.views.tomorrow_partners_views import TomorrowPartnerList
from .views.amount_debit_views import *
from .views.under_review_views import *

router = routers.DefaultRouter()
router.register(r'amount_debit_transactions',AmountDebitTransactionList, "amount_debit_transactions_api")
router.register(r'under_reviews', UnderReviewList, "under_reviews_api")
router.register(r'risk_partners',RiskPartnerList, "risk_partners_api")
router.register(r'to_warned_risk_partners',ToWarnedRiskPartnerList, "to_warned_risk_partners_api")
router.register(r'warned_risk_partners',WarnedRiskPartnerList, "warned_risk_partners_api")
router.register(r'to_terminated_risk_partners',ToTerminatedRiskPartnerList, "to_terminated_risk_partners_api")
router.register(r'tomorrow_partners',TomorrowPartnerList, "tomorrow_partners_api")
router.register(r'today_partners',TodayPartnerList, "today_partners_api")
router.register(r'to_be_transferred',ToBeTransferredList, "to_be_transferred_api")

urlpatterns = [
    path('',include(router.urls)),
]
