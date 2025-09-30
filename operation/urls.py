from django.urls import path, include

from .views import *
from .tests import *

app_name = "operation"

urlpatterns = [
    path('add_partner_advance_activity/', AddPartnerAdvanceActivityView.as_view(), name="add_partner_advance_activity"),
    path('update_leaseflex_automation_partner_advance_activity_leases/', UpdateLeaseflexAutomationPartnerAdvanceActivityLeasesView.as_view(), name="update_leaseflex_automation_partner_advance_activity_leases"),
    path('update_partner_advance_activity_lease_processed_amount/', UpdatePartnerAdvanceActivityLeaseProcessedAmountView.as_view(), name="update_partner_advance_activity_lease_processed_amount"),
    path('update_partner_advance_activity_leases/', UpdatePartnerAdvanceActivityLeasesView.as_view(), name="update_partner_advance_activity_leases"),
    path('export_partner_advance_activities/', ExportPartnerAdvanceActivitiesView.as_view(), name="export_partner_advance_activities"),
    path('partner_advance_activities_excel/', PartnerAdvanceActivitiesExcelView.as_view(), name="partner_advance_activities_excel"),
    path('export_partner_advances/', ExportPartnerAdvancesView.as_view(), name="export_partner_advances"),
    path('partner_advances_excel/', PartnerAdvancesExcelView.as_view(), name="partner_advances_excel"),
    path('update_contract_operation_status/', UpdateContractOperationStatusView.as_view(), name="update_contract_operation_status"),

    path('', include("operation.api.urls")),
]