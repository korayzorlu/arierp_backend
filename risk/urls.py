from django.urls import path, include

from .views import *
from .tests import *

app_name = "risk"

urlpatterns = [
    path('export_risk_partners_for_sms/', ExportRiskPartnersForSMSView.as_view(), name="export_risk_partners_for_sms"),
    path('risk_partners_excel_for_sms/', RiskPartnersExcelForSMSView.as_view(), name="risk_partners_excel_for_sms"),
    path('export_risk_partners/', ExportRiskPartnersView.as_view(), name="export_risk_partners"),
    path('risk_partners_excel/', RiskPartnersExcelView.as_view(), name="risk_partners_excel"),

    path('export_to_warned_risk_partners_for_sms/', ExportToWarnedRiskPartnersForSMSView.as_view(), name="export_to_warned_risk_partners_for_sms"),
    path('to_warned_risk_partners_excel_for_sms/', ToWarnedRiskPartnersExcelForSMSView.as_view(), name="to_warned_risk_partners_excel_for_sms"),
    path('export_to_warned_risk_partners/', ExportToWarnedRiskPartnersView.as_view(), name="export_to_warned_risk_partners"),
    path('to_warned_risk_partners_excel/', ToWarnedRiskPartnersExcelView.as_view(), name="to_warned_risk_partners_excel"),

    path('export_warned_risk_partners_for_sms/', ExportWarnedRiskPartnersForSMSView.as_view(), name="export_warned_risk_partners_for_sms"),
    path('warned_risk_partners_excel_for_sms/', WarnedRiskPartnersExcelForSMSView.as_view(), name="warned_risk_partners_excel_for_sms"),
    path('export_warned_risk_partners/', ExportWarnedRiskPartnersView.as_view(), name="export_warned_risk_partners"),
    path('warned_risk_partners_excel/', WarnedRiskPartnersExcelView.as_view(), name="warned_risk_partners_excel"),

    path('export_to_terminated_risk_partners_for_sms/', ExportToTerminatedRiskPartnersForSMSView.as_view(), name="export_to_terminated_risk_partners_for_sms"),
    path('to_terminated_risk_partners_excel_for_sms/', ToTerminatedRiskPartnersExcelForSMSView.as_view(), name="to_terminated_risk_partners_excel_for_sms"),
    path('export_to_terminated_risk_partners/', ExportToTerminatedRiskPartnersView.as_view(), name="export_to_terminated_risk_partners"),
    path('to_terminated_risk_partners_excel/', ToTerminatedRiskPartnersExcelView.as_view(), name="to_terminated_risk_partners_excel"),

    path('export_amount_debit_transactions/', ExportAmountDebitTransactionsView.as_view(), name="export_amount_debit_transactions"),
    path('amount_debit_transactions_excel/', AmountDebitTransactionsExcelView.as_view(), name="amount_debit_transactions_excel"),
    
    path('', include("risk.api.urls")),
]