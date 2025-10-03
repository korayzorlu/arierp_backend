from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io

from .models import ImportProcess
from .utils.import_utils import BaseImporter
from .utils.export_utils import BaseExporter
from users.models import User
from partners.utils.partner_utils import fetch_partners_from_leaseflex,fetch_partnersi_from_leaseflex,fetch_phone_numbers_from_leaseflex,fetch_phone_numbersi_from_leaseflex
from projects.utils.project_utils import fetch_projects_from_leaseflex
from quotations.utils.quotation_utils import fetch_quotations_from_leaseflex
from quotations.utils.quick_quotation_utils import fetch_quick_quotations_from_leaseflex
from contracts.utils.contract_utils import fetch_contracts_from_leaseflex,fetch_contract_payments_from_leaseflex,fetch_warning_notices_from_leaseflex
from leasing.utils.lease_utils import fetch_leases_from_leaseflex
from leasing.utils.installment_utils import fetch_installments_from_leaseflex

@shared_task(bind=True)
def importData(self,df_json,user_id,app,model_name):
    importer = BaseImporter(user_id=user_id, app=app, model_name=model_name, task_id=self.request.id)
    importer.process_import(df_json)

@shared_task(bind=True)
def exportData(self,user_id,app,model_name,file_name,export_url,params):
    exporter = BaseExporter(user_id=user_id, app=app, model_name=model_name, file_name=file_name, export_url=export_url, task_id=self.request.id,params=params)
    exporter.process_export()

@shared_task()
def fetch_data_from_leaseflex(company):
    fetch_partners_from_leaseflex(company)
    fetch_partnersi_from_leaseflex(company)
    fetch_phone_numbers_from_leaseflex(company)
    fetch_phone_numbersi_from_leaseflex(company)
    fetch_projects_from_leaseflex(company)
    fetch_quick_quotations_from_leaseflex(company)
    fetch_quotations_from_leaseflex(company)
    fetch_contracts_from_leaseflex(company)
    fetch_warning_notices_from_leaseflex(company)
    fetch_leases_from_leaseflex(company)

@shared_task()
def fetch_big_data_from_leaseflex(company):
    fetch_contract_payments_from_leaseflex(company)
    fetch_installments_from_leaseflex(company)