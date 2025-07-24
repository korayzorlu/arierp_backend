from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'contracts', ContractList, "contracts_api")
router.register(r'contract_payments', ContractPaymentList, "contract_payments_api")
router.register(r'warning_notices', WarningNoticeList, "warning_notices_api")

urlpatterns = [
    path('',include(router.urls)),
]
