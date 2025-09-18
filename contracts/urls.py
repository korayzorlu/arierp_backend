from django.urls import path, include

from .views import *
from .tests import *

app_name = "contracts"

urlpatterns = [
    path('add_contract/', AddContractView.as_view(), name="add_contract"),
    path('update_contract/', UpdateContractView.as_view(), name="update_contract"),
    path('delete_contract/', DeleteContractView.as_view(), name="delete_contract"),
    path('delete_contracts/', DeleteContractsView.as_view(), name="delete_contracts"),
    path('delete_all_contracts/', DeleteAllContractsView.as_view(), name="delete_all_contracts"),
    path('contracts_template/', ContractsTemplateView.as_view(), name="contracts_template"),
    path('import_contracts/', ImportContractsView.as_view(), name="import_contracts"),
    path('warning_notice_information/', WarningNoticeInformationView.as_view(), name="warning_notice_information"),

    path('export_contract_payments/', ExportContractPaymentsView.as_view(), name="export_contract_payments"),
    path('contract_payments_excel/', ContractPaymentsExcelView.as_view(), name="contract_payments_excel"),

    path('', include("contracts.api.urls")),
]