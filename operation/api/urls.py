from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'contract_in_suppliers',ContractInSupplierList, "contract_in_suppliers_api")
router.register(r'contract_in_processs',ContractInProcessList, "contract_in_processs_api")
router.register(r'contract_in_archives',ContractInArchiveList, "contract_in_archives_api")
router.register(r'partner_advance_activities',PartnerAdvanceActivityList, "partner_advance_activities_api")
router.register(r'partner_advance_activity_leases',PartnerAdvanceActivityLeaseList, "partner_advance_activity_leases_api")
router.register(r'title_deed_invoice_controls',TitleDeedInvoiceControlList, "title_deed_invoice_controls_api")
router.register(r'untitle_deed_leases',UntitleDeedLeaseList, "untitle_deed_leases_api")
router.register(r'kep_monitorings',KepMonitoringList, "kep_monitorings_api")

urlpatterns = [
    path('',include(router.urls)),
]
