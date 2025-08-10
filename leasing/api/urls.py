from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'leases',LeaseList, "leases_api")
router.register(r'lease_unpages',LeaseUnpageList, "lease_unpages_api")
router.register(r'installments',InstallmentList, "installments_api")
router.register(r'bank_activities',BankActivityList, "bank_activities_api")
router.register(r'bank_activity_leases',BankActivityLeaseList, "bank_activity_leases_api")
router.register(r'risk_partners',RiskPartnerList, "risk_partners_api")
router.register(r'kdv_risk_partners',RiskPartnerKDVList, "kdv_risk_partners_api")
router.register(r'to_warned_risk_partners',ToWarnedRiskPartnerList, "to_warned_risk_partners_api")
router.register(r'warned_risk_partners',WarnedRiskPartnerList, "warned_risk_partners_api")
router.register(r'to_terminated_risk_partners',ToTerminatedRiskPartnerList, "to_terminated_risk_partners_api")
router.register(r'tomorrow_partners',TomorrowPartnerList, "tomorrow_partners_api")
router.register(r'today_partners',TodayPartnerList, "today_partners_api")
router.register(r'delivery_confirms',DeliveryConfirmList, "delivery_confirms_api")
router.register(r'deposit_partners',DepositPartnerList, "deposit_partners_api")

####out api
router.register(r'kizilbuk_risk_partners',OutRiskPartnerList, "kizilbuk_risk_partners_api")

urlpatterns = [
    path('',include(router.urls)),
]
