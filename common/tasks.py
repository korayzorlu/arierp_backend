from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io
from datetime import datetime, timedelta
from decimal import Decimal
import json
import traceback
import time

from .models import ExchangeRate, ImportProcess, Currency
from .utils.import_utils import BaseImporter
from .utils.export_utils import BaseExporter
from .utils.common_utils import get_exchange_rate_for_date
from users.models import User
from partners.utils.partner_utils import fetch_partners_from_leaseflex,fetch_partnersi_from_leaseflex,fetch_phone_numbers_from_leaseflex,fetch_phone_numbersi_from_leaseflex,fetch_partner_advances_from_leaseflex
from projects.utils.project_utils import fetch_projects_from_leaseflex
from projects.utils.parcel_utils import fetch_parcels_from_leaseflex
from projects.utils.real_estate_utils import fetch_real_estates_from_leaseflex
from quotations.utils.quotation_utils import fetch_quotations_from_leaseflex
from quotations.utils.quick_quotation_utils import fetch_quick_quotations_from_leaseflex
from contracts.utils.contract_utils import fetch_contracts_from_leaseflex,fetch_contract_payments_from_leaseflex,fetch_warning_notices_from_leaseflex
from leasing.utils.lease_utils import fetch_leases_from_leaseflex
from leasing.utils.installment_utils import fetch_installments_from_leaseflex
from purchasing.utils.purchase_document_utils import fetch_purchase_documents_from_leaseflex
from accounting.utils.trial_balance_utils import fetch_trial_balances_from_leaseflex
from trade.utils.trade_transaction_utils import fetch_trade_transactions_from_leaseflex
from inventory.utils.item_utils import fetch_items_from_leaseflex

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
    fetch_partner_advances_from_leaseflex(company)
    fetch_projects_from_leaseflex(company)
    fetch_items_from_leaseflex(company)
    fetch_parcels_from_leaseflex(company)
    fetch_real_estates_from_leaseflex(company)
    fetch_quick_quotations_from_leaseflex(company)
    fetch_quotations_from_leaseflex(company)
    fetch_contracts_from_leaseflex(company)
    fetch_warning_notices_from_leaseflex(company)
    fetch_leases_from_leaseflex(company)
    fetch_purchase_documents_from_leaseflex(company)
    fetch_trial_balances_from_leaseflex(company)

@shared_task()
def fetch_big_data_from_leaseflex(company):
    fetch_contract_payments_from_leaseflex(company)
    # fetch_installments_from_leaseflex(company)

@shared_task()
def fetch_very_big_data_from_leaseflex(company):
    fetch_trade_transactions_from_leaseflex(company)

@shared_task()
def fetch_data_for_daily_services(company):
    fetch_exchange_rates("USD")

@shared_task()
def fetch_big_data_for_daily_services(company):
    fetch_installments_from_leaseflex(company)

@shared_task()
def fetch_exchange_rates(target_currency):
    start_date = datetime.now() - timedelta(days=35*1)
    end_date = datetime.now()

    current_date = start_date
    while current_date <= end_date:
        response = get_exchange_rate_for_date(target_currency=target_currency, date=current_date.strftime('%d-%m-%Y'))
        print(response)

        obj = ExchangeRate.objects.select_related('base_currency', 'target_currency').filter(base_currency__code='TRY', target_currency__code=target_currency, date=current_date).first()
        if obj:
            #prev_obj = ExchangeRate.objects.select_related('base_currency', 'target_currency').filter(target_currency__code=target_currency).first()
            prev_obj = ExchangeRate.objects.select_related('base_currency', 'target_currency').filter(
                    base_currency__code='TRY',
                    target_currency__code=target_currency,
                    date__lt=current_date
            ).order_by('-date').first()
            obj.date = current_date
            if response.get('forex_buying', Decimal('0.00')) == Decimal('0.00') and prev_obj:
                obj.forex_buying = prev_obj.forex_buying
            else:
                obj.forex_buying = response.get('forex_buying', Decimal('0.00'))
            if response.get('forex_selling', Decimal('0.00')) == Decimal('0.00') and prev_obj:
                obj.forex_selling = prev_obj.forex_selling
            else:
                obj.forex_selling = response.get('forex_selling', Decimal('0.00'))
            obj.save()
        else:
            new_obj =ExchangeRate.objects.create(
                base_currency = Currency.objects.get(code='TRY'),
                target_currency = Currency.objects.get(code=target_currency),
                date = current_date,
                forex_buying = response.get('forex_buying', Decimal('0.00')),
                forex_selling = response.get('forex_selling', Decimal('0.00'))
            )
            prev_obj = ExchangeRate.objects.select_related('base_currency', 'target_currency').filter(id = new_obj.id - 1).first()
            if response.get('forex_buying', Decimal('0.00')) == Decimal('0.00') and prev_obj:
                new_obj.forex_buying = prev_obj.forex_buying
            if response.get('forex_selling', Decimal('0.00')) == Decimal('0.00') and prev_obj:
                new_obj.forex_selling = prev_obj.forex_selling
            new_obj.save()

        current_date += timedelta(days=1)