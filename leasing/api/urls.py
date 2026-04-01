from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'leases',LeaseList, "leases_api")
router.register(r'projects',ProjectList, "projects_api")
router.register(r'active_leases',ActiveLeaseList, "active_leases_api")
router.register(r'lease_notes', LeaseNoteList, "lease_notes_api")
router.register(r'under_review_leases',UnderReviewLeaseList, "under_review_leases_api")
router.register(r'leases_summary', LeaseSummaryList, "leases_summary_api")
router.register(r'portfolios_summary', PortfolioSummaryList, "portfolios_summary_api")
router.register(r'lease_unpages',LeaseUnpageList, "lease_unpages_api")
router.register(r'installments',InstallmentList, "installments_api")
router.register(r'installments_summary', InstallmentsSummaryList, "installments_summary_api")
router.register(r'bank_activities',BankActivityList, "bank_activities_api")
router.register(r'account_nos', AccountNoList, "account_nos_api")
router.register(r'bank_activity_leases',BankActivityLeaseList, "bank_activity_leases_api")
router.register(r'kdv_risk_partners',RiskPartnerKDVList, "kdv_risk_partners_api")
router.register(r'terminated_summary', TerminatedSummaryList, "terminated_summary_api")
router.register(r'delivery_confirms',DeliveryConfirmList, "delivery_confirms_api")
router.register(r'deposit_partners',DepositPartnerList, "deposit_partners_api")
router.register(r'agreed_terminated_partners',AgreedTerminatedPartnerList, "agreed_terminated_partners_api")

####out api
router.register(r'kizilbuk_risk_partners',OutRiskPartnerList, "kizilbuk_risk_partners_api")

urlpatterns = [
    path('',include(router.urls)),
]
