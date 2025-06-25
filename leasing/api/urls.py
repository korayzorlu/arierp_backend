from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'leases',LeaseList, "leases_api")
router.register(r'installments',InstallmentList, "installments_api")

urlpatterns = [
    path('',include(router.urls)),
]
