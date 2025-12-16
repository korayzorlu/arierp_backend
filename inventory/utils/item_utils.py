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

from inventory.models import *
from leasing.utils.common_utils import get_lease_status_value,status_filter_for_leases
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency,ExchangeRate
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner
from trade.models import TradeTransaction

def fetch_items_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "inventory","sql","envanter.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        items = Item.objects.select_related("company").filter(company__id=int(company))
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        item_by_code = {l.stock_code_id: l for l in items if l.stock_code_id}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.StockCodeId):
                    obj = (item_by_code.get(str(data.StockCodeId)))
                else:
                    obj = None

                if obj:
                    obj.stock_code_id = str(data.StockCodeId) or ""
                    obj.stock_code = str(data.StockCode) or ""
                    obj.stock_name = str(data.StockName) or ""
                    obj.item_group_id = str(data.ItemGroupId) or ""
                    obj.item_group_code = str(data.ItemGroupCode) or ""
                    obj.item_group_name = str(data.ItemGroupName) or ""
                    obj.item_group_type = str(data.ItemGroupType) or ""
                    obj.fixed_asset_group = str(data.FixedAssetGroup) or ""
                    obj.explanation = str(data.Explanation) or ""
                    obj.item_group_type_id = str(data.ItemGroupTypeId) or ""
                    obj.bddk_code = str(data.BDDK_CODE) or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Item(
                        company = company_obj,
                        stock_code_id = str(data.StockCodeId) or "",
                        stock_code = str(data.StockCode) or "",
                        stock_name = str(data.StockName) or "",
                        item_group_id = str(data.ItemGroupId) or "",
                        item_group_code = str(data.ItemGroupCode) or "",
                        item_group_name = str(data.ItemGroupName) or "",
                        item_group_type = str(data.ItemGroupType) or "",
                        fixed_asset_group = str(data.FixedAssetGroup) or "",
                        explanation = str(data.Explanation) or "",
                        item_group_type_id = str(data.ItemGroupTypeId) or "",
                        bddk_code = str(data.BDDK_CODE) or "",
                    ))
                    create_progress += 1
            if update_objs:
                Item.objects.bulk_update(update_objs, [
                    "stock_code_id",
                    "stock_code",
                    "stock_name",
                    "item_group_id",
                    "item_group_code",
                    "item_group_name",
                    "item_group_type",
                    "fixed_asset_group",
                    "explanation",
                    "item_group_type_id",
                    "bddk_code",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Item.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} envanter güncellendi.")
        print(f"Toplam {create_progress} envanter oluşturuldu.")
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