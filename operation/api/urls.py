from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'contract_in_suppliers',ContractInSupplierList, "contract_in_suppliers_api")
router.register(r'contract_in_processs',ContractInProcessList, "contract_in_processs_api")
router.register(r'contract_in_archives',ContractInArchiveList, "contract_in_archives_api")

urlpatterns = [
    path('',include(router.urls)),
]
