from django.urls import path, include

from .views.lease_views import *
from .views.installments_views import *
from .views.bank_activity_views import *
from .tests import *

app_name = "leasing"

urlpatterns = [
    path('add_lease/', AddLeaseView.as_view(), name="add_lease"),
    path('update_lease/', UpdateLeaseView.as_view(), name="update_lease"),
    path('delete_lease/', DeleteLeaseView.as_view(), name="delete_lease"),
    path('delete_leases/', DeleteLeasesView.as_view(), name="delete_leases"),
    path('delete_all_leases/', DeleteAllLeasesView.as_view(), name="delete_all_leases"),
    path('leases_template/', LeasesTemplateView.as_view(), name="leases_template"),
    path('import_leases/', ImportLeasesView.as_view(), name="import_leases"),
    path('update_leaseflex_automation_leases/', UpdateLeaseflexAutomationLeasesView.as_view(), name="update_leaseflex_automation_leases"),
    path('update_lease_processed_amount/', UpdateLeaseProcessedAmountView.as_view(), name="update_lease_processed_amount"),
    path('overdue_information/', OverdueInformationView.as_view(), name="overdue_information"),

    path('add_installment/', AddInstallmentView.as_view(), name="add_installment"),
    path('update_installment/', UpdateInstallmentView.as_view(), name="update_installment"),
    path('delete_installment/', DeleteInstallmentView.as_view(), name="delete_installment"),
    path('delete_installments/', DeleteInstallmentsView.as_view(), name="delete_installments"),
    path('delete_all_installments/', DeleteAllInstallmentsView.as_view(), name="delete_all_installments"),
    path('installments_template/', InstallmentsTemplateView.as_view(), name="installments_template"),
    path('import_installments/', ImportInstallmentsView.as_view(), name="import_installments"),
    path('installment_information/', InstallmentInformationView.as_view(), name="installment_information"),
    
    path('delete_bank_activity/', DeleteBankActivityView.as_view(), name="delete_bank_activity"),
    path('delete_bank_activities/', DeleteBankActivitiesView.as_view(), name="delete_bank_activities"),
    path('delete_all_bank_activities/', DeleteAllBankActivitiesView.as_view(), name="delete_all_bank_activities"),
    path('bank_activities_template/', BankActivitiesTemplateView.as_view(), name="bank_activities_template"),
    path('import_bank_activities/', ImportBankActivitiesView.as_view(), name="import_bank_activities"),
    path('export_bank_activities/', ExportBankActivitiesView.as_view(), name="export_bank_activities"),
    path('bank_activities_excel/', BankActivitiesExcelView.as_view(), name="bank_activities_excel"),
    path('update_leaseflex_automation_bank_activity_leases/', UpdateLeaseflexAutomationBankActivityLeasesView.as_view(), name="update_leaseflex_automation_bank_activity_leases"),
    path('update_bank_activity_lease_processed_amount/', UpdateBankActivityLeaseProcessedAmountView.as_view(), name="update_bank_activity_lease_processed_amount"),
    path('update_bank_activity_leases/', UpdateBankActivityLeasesView.as_view(), name="update_bank_activity_leases"),

    path('export_today_partners/', ExportTodayPartnersView.as_view(), name="export_today_partners"),
    path('today_partners_excel/', TodayPartnersExcelView.as_view(), name="today_partners_excel"),

    path('export_tomorrow_partners/', ExportTomorrowPartnersView.as_view(), name="export_tomorrow_partners"),
    path('tomorrow_partners_excel/', TomorrowPartnersExcelView.as_view(), name="tomorrow_partners_excel"),

    path('export_risk_partners/', ExportRiskPartnersView.as_view(), name="export_risk_partners"),
    path('risk_partners_excel/', RiskPartnersExcelView.as_view(), name="risk_partners_excel"),

    path('export_kdv_risk_partners/', ExportKDVRiskPartnersView.as_view(), name="export_kdv_risk_partners"),
    path('risk_kdv_partners_excel/', KDVRiskPartnersExcelView.as_view(), name="kdv_risk_partners_excel"),

    path('export_to_warned_risk_partners/', ExportToWarnedRiskPartnersView.as_view(), name="export_to_warned_risk_partners"),
    path('to_warned_risk_partners_excel/', ToWarnedRiskPartnersExcelView.as_view(), name="to_warned_risk_partners_excel"),

    path('export_warned_risk_partners/', ExportWarnedRiskPartnersView.as_view(), name="export_warned_risk_partners"),
    path('warned_risk_partners_excel/', WarnedRiskPartnersExcelView.as_view(), name="warned_risk_partners_excel"),

    path('export_to_terminated_risk_partners/', ExportToTerminatedRiskPartnersView.as_view(), name="export_to_terminated_risk_partners"),
    path('to_terminated_risk_partners_excel/', ToTerminatedRiskPartnersExcelView.as_view(), name="to_terminated_risk_partners_excel"),

    path('', include("leasing.api.urls")),
]