from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import make_aware

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict
import os
import traceback
import gc
import string
import random

from leasing.models import *
from leasing.utils.common_utils import get_lease_status_value,status_filter_for_leases,days_in_month
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency,ExchangeRate,TufeRate
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner
from trade.models import TradeTransaction

def fetch_leases_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "leasing","sql","kira_planlari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        leases = Lease.objects.select_related("status","company","contract","currency").filter(company__id=int(company))
        partners = Partner.objects.select_related().filter(company__id=int(company))
        contracts = Contract.objects.select_related().filter(company__id=int(company))
        items = Item.objects.select_related().filter(company__id=int(company))
        statuses = Status.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        lease_by_code = {l.lease_id: l for l in leases if l.lease_id}
        del leases
        gc.collect()

        contracts_dict = {c.code: c for c in contracts}
        partners_dict = {p.crm_code: p for p in partners}
        items_dict = {i.stock_code_id: i for i in items}
        statuses_dict = {s.name: s for s in statuses}
        currencies_dict = {c.code: c for c in currencies}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.OperationProjectId):
                    obj = (lease_by_code.get(str(data.OperationProjectId)))
                else:
                    obj = None

                # leases_count = Lease.objects.select_related().filter(
                #     main_lease_id=str(data.MainLopId),
                #     is_last_project = True
                # ).aggregate(
                #     count=Count('id')
                # )['count']

                if obj:
                    obj.lease_id = str(data.OperationProjectId) or ""
                    obj.main_lease_id = str(data.MainLopId) or ""
                    obj.code = str(data.OperationProjectCode) or ""
                    obj.contract = contracts_dict.get(str(data.ContractHeaderCode))
                    obj.vendor = partners_dict.get(str(data.Vendor))
                    obj.item = items_dict.get(str(data.Project))
                    obj.type = str(data.TypeName) or ""
                    obj.vat = safe_decimal(data.VatRate)
                    obj.activation_date = data.ActivationDate.date() if data.ActivationDate else None
                    obj.lease_status = get_lease_status_value(str(data.RiskIncludingTypeName)) or None
                    obj.lease_status_update_date = make_aware(data.RiskIncludingLastUpdateDate) if data.RiskIncludingLastUpdateDate else None
                    obj.currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode)
                    obj.musteri_baz_maliyet = safe_decimal(data.CustomerBaseCost)
                    obj.vade = int(data.PaymentCount) or ""
                    obj.leasing_rate = safe_decimal(data.AnnualRate)
                    obj.irr = safe_decimal(data.OperationBaseIRR)
                    obj.status = statuses_dict.get(str(data.SubStatuteName)) if data.SubStatuteName else None
                    obj.leasing_type = str(data.LeasingTypeName) or ""
                    obj.application_no = str(data.ApplicationID) or ""
                    obj.is_last_project = True if str(data.IS_LAST_PROJECT) == "1" else False
                    obj.current_request = str(data.CurrentRequest) or ""
                    #obj.transfer_count = leases_count - 1 if leases_count > 0 else 0
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Lease(
                        company = company_obj,
                        lease_id = str(data.OperationProjectId) or "",
                        main_lease_id = str(data.MainLopId) or "",
                        code = str(data.OperationProjectCode) or "",
                        contract = contracts_dict.get(str(data.ContractHeaderCode)),
                        vendor = partners_dict.get(str(data.Vendor)),
                        item = items_dict.get(str(data.Project)),
                        type = str(data.TypeName) or "",
                        vat = safe_decimal(data.VatRate),
                        activation_date = data.ActivationDate.date() if data.ActivationDate else None,
                        lease_status = get_lease_status_value(str(data.RiskIncludingTypeName)) or None,
                        lease_status_update_date = make_aware(data.RiskIncludingLastUpdateDate) if data.RiskIncludingLastUpdateDate else None,
                        currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode),
                        musteri_baz_maliyet = safe_decimal(data.CustomerBaseCost),
                        vade = int(data.PaymentCount) or "",
                        leasing_rate = safe_decimal(data.AnnualRate),
                        irr = safe_decimal(data.OperationBaseIRR),
                        status = statuses_dict.get(normalize(data.SubStatuteName)),
                        leasing_type = str(data.LeasingTypeName) or "",
                        application_no = str(data.ApplicationID) or "",
                        is_last_project = True if str(data.IS_LAST_PROJECT) == "1" else False,
                        current_request = str(data.CurrentRequest) or "",
                        #transfer_count = leases_count - 1 if leases_count > 0 else 0,
                    ))
                    create_progress += 1
            if update_objs:
                Lease.objects.bulk_update(update_objs, [
                    "lease_id",
                    "main_lease_id",
                    "code",
                    "contract",
                    "vendor",
                    "item",
                    "type",
                    "vat",
                    "activation_date",
                    "lease_status",
                    "lease_status_update_date",
                    "currency",
                    "musteri_baz_maliyet",
                    "vade",
                    "leasing_rate",
                    "irr",
                    "status",
                    "leasing_type",
                    "application_no",
                    "is_last_project",
                    "current_request"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Lease.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        del lease_by_code
        gc.collect()
        print(f"Toplam {update_progress} kira planı güncellendi.")
        print(f"Toplam {create_progress} kira planı oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def fetch_interest_rates_from_leaseflex(company,BATCH_SIZE=1000):
    pass

def fetch_exchanged_amounts_utils(company,BATCH_SIZE=1000):
    try:
        objs = Lease.objects.select_related("company","currency").filter(company__id=int(company),overdue_amount__gt=0,is_last_project=True,currency__code__in=['TRY'])
        exchange_rates = ExchangeRate.objects.select_related("target_currency").filter(target_currency__code="USD")

        exchange_rates_dict = {e.date: e for e in exchange_rates}

        update_progress = 0

        update_objs = []
        for index,obj in enumerate(objs):
            installments = Installment.objects.select_related("lease").filter(
                lease=obj,
                payment_date__lte=date.today()
            )

            installments_total = installments.aggregate(total_amount=Sum('amount'))

            exchanged_amount_due_to_date = Decimal('0.00')
            for installment in installments:
                exchange_rate = exchange_rates_dict.get(installment.payment_date)
                exchanged_amount_due_to_date += installment.amount / exchange_rate.forex_buying if exchange_rate else installment.amount
            
            # obj.contract.code örneği: "1234", "1234/1", "1234/2" olabilir.
            # Sadece ana kodu (ör: "1234") alıp filtrele
            ana_kod = obj.contract.code.split('/')[0] if obj.contract and obj.contract.code else None
            # Eğer contract.code '/' içeriyorsa, '/' karakterinden önceki kısmı al
            # Örneğin: "1234/2" -> "1234"
            # Eğer '/' yoksa, kodu olduğu gibi kullan
            trade_transactions = TradeTransaction.objects.select_related("lease").filter(
                lease__contract__code__startswith=ana_kod,
                posting_group_name='Kira',
                amount_type='0',
                due_date__lte=timezone.now()
            )

            trade_transactions_total = trade_transactions.aggregate(total_amount=Sum('amount'))

            exchanged_amount_paid_to_date = Decimal('0.00')
            for transaction in trade_transactions:
                exchange_rate = exchange_rates_dict.get(transaction.due_date.date())
                exchanged_amount_paid_to_date += transaction.amount / exchange_rate.forex_buying if exchange_rate else transaction.amount

            kur_kaybi_yuzde = Decimal('0.00')
            if exchanged_amount_due_to_date != Decimal('0.00'):
                kur_kaybi_yuzde = exchanged_amount_paid_to_date / exchanged_amount_due_to_date * Decimal('100.00')
            else:
                kur_kaybi_yuzde = Decimal('0.00')

            obj.odenmesi_gereken_yerel = installments_total['total_amount'] or Decimal('0.00')
            obj.odenmesi_gereken_usd = exchanged_amount_due_to_date
            obj.odenen_yerel = trade_transactions_total['total_amount'] or Decimal('0.00')
            obj.odenen_usd = exchanged_amount_paid_to_date
            obj.geciken_usd = obj.overdue_amount / (exchange_rates_dict.get(date.today()).forex_buying if exchange_rates_dict.get(date.today()) else Decimal('1.00'))
            obj.geciken_odenmesi_gereken_usd = exchanged_amount_due_to_date - exchanged_amount_paid_to_date
            obj.kur_kaybi = exchanged_amount_due_to_date - exchanged_amount_paid_to_date - (obj.overdue_amount / (exchange_rates_dict.get(date.today()).forex_buying if exchange_rates_dict.get(date.today()) else Decimal('1.00')))
            obj.kur_kaybi_yuzde = kur_kaybi_yuzde

            update_objs.append(obj)
            update_progress += 1
        if update_objs:
            Lease.objects.bulk_update(update_objs, [
                "odenmesi_gereken_yerel",
                "odenmesi_gereken_usd",
                "odenen_yerel",
                "odenen_usd",
                "geciken_usd",
                "geciken_odenmesi_gereken_usd",
                "kur_kaybi",
                "kur_kaybi_yuzde",
            ])

        print(f"Toplam {update_progress} kira planı kur kayıpları güncellendi.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def fetch_tufe_exchanged_amounts_utils(company,BATCH_SIZE=1000):
    try:
        objs = Lease.objects.select_related("company","currency").filter(company__id=int(company),overdue_amount__gt=0,is_last_project=True,currency__code__in=['TRY'])
        tufe_rate = TufeRate.objects.select_related().order_by('-date').first()

        update_progress = 0

        update_objs = []
        for index,obj in enumerate(objs):
            overdue_date = timezone.now().date() - timedelta(days=obj.overdue_days)
            # Eğer gecikme tarihi içinde bulunduğumuz ay ise, bir önceki ayı ve yılı al
            today = timezone.now().date()
            if overdue_date.year == today.year and overdue_date.month == today.month:
                if overdue_date.month == 1:
                    overdue_year = overdue_date.year - 1
                    overdue_month = 12
                else:
                    overdue_year = overdue_date.year
                    overdue_month = overdue_date.month - 1
            else:
                overdue_year = overdue_date.year
                overdue_month = overdue_date.month

            # 1. Gecikmenin başlangıcındaki ay içerisindeki hesap
            tufe_rate_at_overdue_start = TufeRate.objects.select_related().filter(date__year=overdue_year, date__month=overdue_month).first()
            daily_rate_at_overdue_start = tufe_rate_at_overdue_start.change_rate / Decimal(str(days_in_month(overdue_date)))
            days_in_overdue_start_month = days_in_month(overdue_date) - overdue_date.day + 1
            tufeli_amount_start_month = obj.overdue_amount * (Decimal('1.00') + (daily_rate_at_overdue_start * Decimal(str(days_in_overdue_start_month))) / Decimal('100.00'))

            # 2. Gecikmenin devam ettiği aylar için bugünkü aya kadar olan hesap
            tufeli_amount = Decimal('0.00') + tufeli_amount_start_month
            for year in range(overdue_year, today.year + 1):
                start_month = overdue_month + 1 if year == overdue_year else 1
                end_month = today.month if year == today.year else 12
                for month in range(start_month, end_month):
                    tufe_rate_current = TufeRate.objects.select_related().filter(date__year=year, date__month=month).first()
                    tufeli_amount = tufeli_amount * (Decimal('1.00') + tufe_rate_current.change_rate / Decimal('100.00'))
            
            # 3. Bugünkü ay için günlük hesap
            daily_rate_current_month = tufe_rate.change_rate / Decimal(str(days_in_month(today)))
            tufeli_amount = tufeli_amount * (Decimal('1.00') + (daily_rate_current_month * Decimal(str(today.day))) / Decimal('100.00'))
            
            #print(f"Lease {obj.code} gecikme günü: {obj.overdue_days} - gecikme tutarı: {obj.overdue_amount} - Tüfeli Amount Total: {tufeli_amount}")

            obj.tufeli_geciken = tufeli_amount

            update_objs.append(obj)
            update_progress += 1
        if update_objs:
            Lease.objects.bulk_update(update_objs, [
                "tufeli_geciken",
            ])
            pass

        print(f"Toplam {update_progress} kira planı tüfe kayıpları güncellendi.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())