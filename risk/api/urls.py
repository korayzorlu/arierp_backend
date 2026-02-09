from django.urls import path, include
from rest_framework import routers

from risk.api.views.to_be_transferred_views import *
from risk.api.views.to_terminated_risk_partners_views import *
from risk.api.views.terminated_leases_views import *
from risk.api.views.exchanged_leases_views import *
from risk.api.views.tufe_exchanged_leases_views import *
from risk.api.views.warned_risk_partners_views import *
from risk.api.views.risk_partners_views import *
from risk.api.views.to_warned_risk_partnes_views import *
from risk.api.views.today_partners_views import *
from risk.api.views.tomorrow_partners_views import *
from risk.api.views.title_deed_confirm_views import *
from .views.amount_debit_views import *
from .views.under_review_views import *

router = routers.DefaultRouter()
router.register(r'amount_debit_transactions',AmountDebitTransactionList, "amount_debit_transactions_api")
router.register(r'under_reviews', UnderReviewList, "under_reviews_api")
router.register(r'risk_partners',RiskPartnerList, "risk_partners_api")
router.register(r'to_warned_risk_partners',ToWarnedRiskPartnerList, "to_warned_risk_partners_api")
router.register(r'deposite_to_warned_risk_partners',DepositeToWarnedRiskPartnerList, "deposite_to_warned_risk_partners_api")
router.register(r'kep_to_warned_risk_partners',KepToWarnedRiskPartnerList, "kep_to_warned_risk_partners_api")
router.register(r'posta_to_warned_risk_partners',PostaToWarnedRiskPartnerList, "posta_to_warned_risk_partners_api")
router.register(r'warned_risk_partners',WarnedRiskPartnerList, "warned_risk_partners_api")
router.register(r'comprehensive_warned_risk_partners',ComprehensiveWarnedRiskPartnerList, "comprehensive_warned_risk_partners_api")
router.register(r'to_terminated_risk_partners',ToTerminatedRiskPartnerList, "to_terminated_risk_partners_api")
router.register(r'terminated_leases',TerminatedLeaseList, "terminated_leases_api")
router.register(r'exchanged_leases',ExchangedLeaseList, "exchanged_leases_api")
router.register(r'tufe_exchanged_leases',TufeExchangedLeaseList, "tufe_exchanged_leases_api")
router.register(r'tomorrow_partners',TomorrowPartnerList, "tomorrow_partners_api")
router.register(r'today_partners',TodayPartnerList, "today_partners_api")
router.register(r'to_be_transferred',ToBeTransferredList, "to_be_transferred_api")
router.register(r'title_deed_confirms',TitleDeedConfirmList, "title_deed_confirms_api")

urlpatterns = [
    path('',include(router.urls)),
]
