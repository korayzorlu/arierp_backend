from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'leases',LeaseList, "leases_api")
router.register(r'lease_unpages',LeaseUnpageList, "lease_unpages_api")
router.register(r'installments',InstallmentList, "installments_api")
router.register(r'bank_activities',BankActivityList, "bank_activities_api")

urlpatterns = [
    path('',include(router.urls)),
]
