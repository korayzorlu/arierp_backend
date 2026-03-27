from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum,F,ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
from django.utils.timezone import make_aware
from django.utils import timezone

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
import requests
import xmltodict
import json

from leasing.models import *
from leasing.utils.common_utils import get_lease_status_value,status_filter_for_leases,days_in_month
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency,ExchangeRate,TufeRate
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner
from trade.models import TradeTransaction
from contracts.models import WarningNotice,ComprehensiveWarningNotice

def fetch_leases_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "leasing","sql","kira_planlari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        currencies = Currency.objects.select_related().all()
        warning_notices = WarningNotice.objects.select_related().all()
        comprehensive_warning_notices = ComprehensiveWarningNotice.objects.select_related().all()
        trade_transactions = TradeTransaction.objects.select_related("lease").filter(amount_type = '0', posting_group_name='Kira').only("amount", "lease", "lease__lease_id")
        installments = Installment.objects.select_related("lease").filter(type__in = ['1','2']).only("amount", "type", "lease", "lease__lease_id")
        transfer_installments = Installment.objects.select_related("lease").filter(type = '5').only("amount", "type", "lease", "lease__lease_id")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()
        currencies_dict = {c.code: c for c in currencies}
        warning_notices_dict = {w.contract.contract_id: w for w in warning_notices}
        comprehensive_warning_notices_dict = {cw.contract.contract_id: cw for cw in comprehensive_warning_notices}
        trade_transactions_dict = defaultdict(list)
        for tt in trade_transactions:
            if tt.lease and tt.lease.lease_id:
                trade_transactions_dict[tt.lease.lease_id].append(tt)
        installments_dict = defaultdict(list)
        for installment in installments:
            if installment.lease and installment.lease.lease_id:
                installments_dict[installment.lease.lease_id].append(installment)
        transfer_installments_dict = defaultdict(list)
        for t_installment in transfer_installments:
            if t_installment.lease and t_installment.lease.lease_id:
                transfer_installments_dict[t_installment.lease.lease_id].append(t_installment)

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            # 1. codes
            lease_codes = [r.OperationProjectId for r in records]
            contract_codes = [r.ContractHeaderCode for r in records]
            partner_codes = [r.Vendor for r in records]
            item_codes = [r.Project for r in records]
            status_codes = [r.SubStatuteName for r in records]
            # 2. querysets
            leases = Lease.objects.select_related().filter(lease_id__in=lease_codes)
            contracts = Contract.objects.select_related().filter(code__in=contract_codes)
            partners = Partner.objects.select_related().filter(crm_code__in=partner_codes)
            items = Item.objects.select_related().filter(stock_code_id__in=item_codes)
            statuses = Status.objects.select_related().filter(name__in=status_codes)
            # 3. dicts
            lease_dict = {l.lease_id: l for l in leases}
            contracts_dict = {c.code: c for c in contracts}
            partners_dict = {p.crm_code: p for p in partners}
            items_dict = {i.stock_code_id: i for i in items}
            statuses_dict = {s.name: s for s in statuses}
            for index,data in enumerate(records):
                if str(data.OperationProjectId):
                    obj = (lease_dict.get(str(data.OperationProjectId)))
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
                    obj.block = str(data.BLOCK_NO) or ""
                    obj.unit = str(data.FREE_PART_NO) or ""
                    obj.island = str(data.ISLAND_NO) or ""
                    obj.parcel = str(data.PARCEL_NO) or ""
                    obj.city = str(data.CityName) or ""
                    obj.district = str(data.DistrictName) or ""
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
                    obj.notary_public_date = data.NotaryPublicDate.date() if data.NotaryPublicDate else None
                    obj.bbsn = str(data.BBSN_NO) or ""
                    #obj.transfer_count = leases_count - 1 if leases_count > 0 else 0

                    #ödeme kontrolü
                    obj_trade_transactions = trade_transactions_dict.get(obj.lease_id, [])
                    if obj_trade_transactions:
                        paid_amount = sum([tt.amount for tt in obj_trade_transactions], Decimal('0.00'))
                    else:
                        paid_amount = Decimal('0.00')
                    obj.paid_amount = paid_amount

                    #taksit kontrolü
                    obj_installments = installments_dict.get(obj.lease_id, [])
                    if obj_installments:
                        installment_amount = sum([inst.amount for inst in obj_installments], Decimal('0.00'))
                    else:
                        installment_amount = Decimal('0.00')
                    obj.installment_amount = installment_amount

                    #devir bedeli kontrolü
                    obj_t_installments = transfer_installments_dict.get(obj.lease_id, [])
                    if obj_t_installments:
                        transfer_amount = sum([inst.amount for inst in obj_t_installments], Decimal('0.00'))
                    else:
                        transfer_amount = Decimal('0.00')
                    obj.transfer_amount = transfer_amount

                    #ihtar kontrolü
                    wns = warning_notices_dict.get(obj.contract.contract_id)
                    cwns = comprehensive_warning_notices_dict.get(obj.contract.contract_id)
                    if not wns and not cwns:
                        obj.warning_notice_status = 'ihtar_yok'
                    elif wns and not cwns:
                        obj.warning_notice_status = 'normal_ihtar'
                    elif cwns:
                        obj.warning_notice_status = 'kapsamli_ihtar'

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
                        block = str(data.BLOCK_NO) or "",
                        unit = str(data.FREE_PART_NO) or "",
                        island = str(data.ISLAND_NO) or "",
                        parcel = str(data.PARCEL_NO) or "",
                        city = str(data.CityName) or "",
                        district = str(data.DistrictName) or "",
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
                        notary_public_date = data.NotaryPublicDate.date() if data.NotaryPublicDate else None,
                        bbsn = str(data.BBSN_NO) or "",
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
                    "block",
                    "unit",
                    "island",
                    "parcel",
                    "city",
                    "district",
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
                    "current_request",
                    "notary_public_date",
                    "bbsn",
                    "paid_amount",
                    "installment_amount",
                    "transfer_amount",
                    "warning_notice_status"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Lease.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

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
        objs = Lease.objects.select_related("company","currency").filter(company__id=int(company),is_last_project=True,currency__code__in=['TRY'])
        #objs = objs.filter(contract__code__in = ['57796','57797','57798'])
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
                # amount_type='0',
                due_date__lte=timezone.now()
            ).exclude(delete_status__in=['2'])
            
            trade_transactions_total = trade_transactions.aggregate(total_amount=Sum('amount'))

            exchanged_amount_paid_to_date = Decimal('0.00')
            for transaction in trade_transactions:
                exchange_rate = exchange_rates_dict.get(transaction.due_date.date())
                if transaction.amount_type == '0':  # Tahsilat
                    exchanged_amount_paid_to_date += transaction.amount / exchange_rate.forex_buying if exchange_rate else transaction.amount
                elif transaction.amount_type == '1' and (transaction.document_no == '' or transaction.document_no is None):  # İade veya diğer işlemler
                    exchanged_amount_paid_to_date -= transaction.amount / exchange_rate.forex_buying if exchange_rate else transaction.amount

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
        objs = Lease.objects.select_related("company","currency").filter(
            Q(company__id=int(company)),
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            #Q(overdue_amount__gt=0),
            Q(is_last_project=True),
            Q(currency__code__in=['TRY'])
        )
        #objs = objs.filter(contract__code__in = ['57796','57797','57798'])
        tufe_rate_last = TufeRate.objects.select_related().filter(date__lte=date.today()).order_by("-date").first()

        update_progress = 0

        update_objs = []
        for index,obj in enumerate(objs):
            overdue_date = timezone.now().date() - timedelta(days=obj.overdue_days)
            today = timezone.now().date()
            installments = Installment.objects.select_related("lease").filter(
                lease=obj,
                payment_date__lte=date.today()
            )
            
            end_karsiligi_toplam = Decimal('0.00')
            for installment in installments:
                tufe_rate = TufeRate.objects.select_related().filter(date__lte=installment.payment_date).order_by("-date").first()
                end_karsiligi_toplam += (installment.amount * (tufe_rate_last.value if tufe_rate_last else Decimal('1.00'))) / (tufe_rate.value if tufe_rate and tufe_rate.value != 0 else Decimal('1.00'))

            ana_kod = obj.contract.code.split('/')[0] if obj.contract and obj.contract.code else None

            trade_transactions = TradeTransaction.objects.select_related("lease").filter(
                lease__contract__code__startswith=ana_kod,
                posting_group_name='Kira',
                # amount_type='0',
                due_date__lte=timezone.now()
            ).exclude(delete_status__in=['2'])

            end_karsiligi_tahsilat_toplam = Decimal('0.00')
            for trade_transaction in trade_transactions:
                tufe_rate = TufeRate.objects.select_related().filter(date__lte=trade_transaction.due_date).order_by("-date").first()
                if trade_transaction.amount_type == '0':  # Tahsilat
                    end_karsiligi_tahsilat_toplam += (trade_transaction.amount * (tufe_rate_last.value if tufe_rate_last else Decimal('1.00'))) / (tufe_rate.value if tufe_rate and tufe_rate.value != 0 else Decimal('1.00'))
                elif trade_transaction.amount_type == '1' and (trade_transaction.document_no == '' or trade_transaction.document_no is None):
                    end_karsiligi_tahsilat_toplam -= (trade_transaction.amount * (tufe_rate_last.value if tufe_rate_last else Decimal('1.00'))) / (tufe_rate.value if tufe_rate and tufe_rate.value != 0 else Decimal('1.00'))

            fark = end_karsiligi_toplam - end_karsiligi_tahsilat_toplam

            obj.tufe_odenmesi_gereken = end_karsiligi_toplam
            obj.tufe_odenen = end_karsiligi_tahsilat_toplam
            obj.tufe_fark = fark

            update_objs.append(obj)
            update_progress += 1
        if update_objs:
            Lease.objects.bulk_update(update_objs, [
                "tufe_fark",
                "tufe_odenmesi_gereken",
                "tufe_odenen"
            ])

        print(f"Toplam {update_progress} kira planı tüfe kayıpları güncellendi.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def fetch_tufe_exchanged_amounts_utilss(company,BATCH_SIZE=1000):
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
            if TufeRate.objects.select_related().filter(date__year=overdue_year, date__month=overdue_month).exists():
                tufe_rate_at_overdue_start = TufeRate.objects.select_related().filter(date__year=overdue_year, date__month=overdue_month).first()
            else:
                tufe_rate_at_overdue_start = TufeRate.objects.select_related().filter(date__year=overdue_year if overdue_month > 1 else overdue_year - 1, date__month=overdue_month - 1 if overdue_month > 1 else 12).first()
            daily_rate_at_overdue_start = (tufe_rate_at_overdue_start.change_rate if tufe_rate_at_overdue_start else Decimal('0.00')) / Decimal(str(days_in_month(overdue_date)))
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

def fetch_leases_from_ifs(company,BATCH_SIZE=1000):
    try:
        objs = Lease.objects.select_related().filter(is_last_project=True,bbsn__isnull=False).exclude(bbsn="").only('bbsn')

        update_progress = 0
        update_objs = []
        for obj in objs:
            url = f"http://192.168.48.49/SinpasCrmService/crm.asmx/SozlesmeNoGetir?BbsnNo={obj.bbsn}"

            response = requests.get(url)
            data_dict = xmltodict.parse(response.text)
            #json_data = json.dumps(data_dict, ensure_ascii=False, indent=2)

            result = data_dict["SozlesmeNoGetirSonucu"]

            obj.crm_no = result.get("SozlesmeNo", None)

            update_objs.append(obj)
            update_progress += 1

        if update_objs:
            Lease.objects.bulk_update(update_objs, [
                "crm_no",
            ])

        print(f"Toplam {update_progress} kira planı güncellendi.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def fetch_purchase_payments_from_ifs(company,BATCH_SIZE=1000):
    try:
        objs = Lease.objects.select_related().filter(crm_no__isnull=False).only('crm_no')

        update_progress = 0
        update_objs = []
        for obj in objs:
            url = f"http://192.168.48.49/SinpasCrmService/crm.asmx/AriTahsilatGetir?SozlesmeNo={obj.crm_no}&Tarih={timezone.now().date()}"

            response = requests.get(url)
            data_dict = xmltodict.parse(response.text)
            #json_data = json.dumps(data_dict, ensure_ascii=False, indent=2)

            result = data_dict["AriTahsilatSonucu"]

            obj.ifs_tahsilat = Decimal(result.get("IfsTahsilatTutari", Decimal('0.00')))

            update_objs.append(obj)
            update_progress += 1

        if update_objs:
            Lease.objects.bulk_update(update_objs, [
                "ifs_tahsilat",
            ])

        print(f"Toplam {update_progress} kira planı güncellendi.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def get_future_payments(lease_id, from_date=None):
    """
    Belirtilen tarihten (varsayılan: bugün) itibaren gelecekteki ödemeleri getirir.
    """
    if from_date is None:
        from_date = timezone.now().date()

    lease = Lease.objects.filter(lease_id=lease_id).first()

    if not lease:
        return Decimal('0.00')
    
    total = Installment.objects.select_related("lease").filter(lease=lease, payment_date__gte=from_date).aggregate(total_amount=Sum('amount'))['total_amount'] or Decimal('0.00')
    
    return total

def get_lease_delay(company,lease_id,as_of=None):
    as_of = as_of or timezone.now().date()

    lease = Lease.objects.select_related().filter(company__id=int(company),lease_id=lease_id).first()

    if lease:
        installments = (
            lease.lease_installments
            .filter(Q(payment_date__lt=as_of) & ~Q(type='5'))
            .order_by("sequency")
            .values_list("payment_date", "amount", "payment", "vat_amount")
        )

        due_total = Decimal('0.00')
        installment_list = []
        for payment_date, amount, payment, vat_amount in installments:
            due_total +=  payment + vat_amount
            installment_list.append((payment_date, payment + vat_amount))

        ana_kod = lease.contract.code.split('/')[0] if lease.contract and lease.contract.code else None

        trade_transactions = TradeTransaction.objects.select_related("lease").filter(
            lease__contract__code__startswith=ana_kod,
            posting_group_name='Kira',
            due_date__lt=as_of
        ).exclude(delete_status__in=['2'])

        paid_total = Decimal('0.00')
        for transaction in trade_transactions:
            if transaction.amount_type == '0':
                paid_total += transaction.amount
            elif transaction.amount_type == '1' and (transaction.document_no == '' or transaction.document_no is None):
                paid_total -= transaction.amount

        remaining_paid = paid_total

        first_overdue_due_date = None
        for payment_date, amount in installment_list:
            if remaining_paid >= amount:
                remaining_paid -= amount
            else:
                first_overdue_due_date = payment_date
                break
        
        delay = (as_of - first_overdue_due_date).days if first_overdue_due_date else 0

        print(f"ödenmesi gereken: {due_total} - ödenen: {paid_total} - gecikme: {due_total - paid_total} - gecikme gün sayısı: {delay}")

def get_faulty_lease(company):
    # Farkın mutlak değeri 10'dan büyük olanları bul
    objs = Installment.objects.select_related().annotate(
        diff=ExpressionWrapper(F('amount') - (F('payment') + F('vat_amount')), output_field=DecimalField())
    ).filter(
        Q(company__id=int(company)),
        Q(lease__is_last_project=True)
    ).exclude(
        diff__gte=-10, diff__lte=10
    )

    for obj in objs:
        print(f"Kira: {obj.lease.code} - Taksit No: {obj.sequency} - Tutar: {obj.payment} - KDV Tutarı: {obj.vat_amount} - Toplam Tutar: {obj.amount}")

    print(f"Toplam {objs.count()} hatalı kira taksiti bulundu.")

def get_leases_excel_file(company):
    company = Company.objects.select_related().filter(id=int(company)).first()

    objs = Lease.objects.select_related("contract","currency").filter(
        Q(activation_date__gte=date(2025, 1, 1)) &
        Q(activation_date__lte=date(2025, 12, 31))
    ).order_by("activation_date")
    data = {
        "Kira Planı": [],
        "Sözleşme No": [],
        "Sözleşme Tarihi": [],
        "Müşteri İsim": [],
        "Müşteri TC/VKN": [],
        "Proje": [],
        "Sözleşme Bedeli": [],
        "Döviz Cinsi": [],
        "Statü": [],
        
    }

    for obj in objs:
        if obj.contract and obj.contract.partner:
            if obj.contract.partner.tc_vkn_no and obj.contract.partner.tc_vkn_no != "":
                data["Müşteri TC/VKN"].append(obj.contract.partner.tc_vkn_no)
            elif obj.contract.partner.vat_no and obj.contract.partner.vat_no != "":
                data["Müşteri TC/VKN"].append(obj.contract.partner.vat_no)
            else:
                    data["Müşteri TC/VKN"].append("")
        data["Müşteri İsim"].append(obj.contract.partner.name if obj.contract and obj.contract.partner else "")
        data["Proje"].append(obj.item.stock_name if obj.item else "")
        data["Sözleşme Bedeli"].append(obj.total_payment)
        data["Döviz Cinsi"].append(obj.currency.code)
        data["Kira Planı"].append(obj.code)
        data["Sözleşme No"].append(obj.contract.code if obj.contract else "")
        data["Sözleşme Tarihi"].append(obj.activation_date.strftime('%d.%m.%Y') if obj.activation_date else "")
        data["Statü"].append(obj.get_lease_status_display())

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Sözleşme Bedeli",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(company.uuid), "leasing", "leases", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-kira-planlari-ozel.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sayfa', index=False)

        # Workbook'u al
        workbook = writer.book
        worksheet = writer.sheets['Sayfa']

        # Kolon isimlerine göre format uygula
        for idx, col in enumerate(df.columns, 1):  # enumerate 1'den başlıyor
            if col in numeric_columns:
                for cell in worksheet.iter_cols(min_col=idx, max_col=idx, min_row=2):
                    for c in cell:
                        c.number_format = '#,##0.00'   # İstediğin format

def fix_last_projects_arinet(company):
    try:
        objs = Lease.objects.select_related().filter(is_last_project = True)
        objs.update(is_last_project_arinet = False)

        for obj in objs:
            last_lease = Lease.objects.select_related().filter(main_lease_id=obj.main_lease_id).annotate(lease_id_int=Cast("lease_id", IntegerField())).order_by("-lease_id_int").first()

            if last_lease.lease_id == obj.lease_id:
                obj.is_last_project_arinet = True
                obj.save()
            else:
                obj.is_last_project_arinet = False
                obj.save()
                last_lease.is_last_project_arinet = True
                last_lease.save()

    except Exception as e:
        print(e)
        print(traceback.format_exc())

def set_title_deed_delivery(company):
    excel_file = pd.ExcelFile("files/tapusu-cikanlar.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/tapusu-cikanlar.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    olmayanlar = 0
    for index,row in df.iterrows():
        if Contract.objects.filter(code = str(row['Kira plani kodu']).replace(".0","")).exists():
            if not Lease.objects.filter(contract__code = str(row['Kira plani kodu']).replace(".0",""), is_last_project=True).exists():
                print(str(row['Kira plani kodu']))
                olmayanlar += 1
    print(olmayanlar)
            

    # leases = Lease.objects.select_related().filter(is_last_project = True)
    # leases.update(is_title_deed_delivered = False)

    # contracts = Contract.objects.select_related().prefetch_related("contract_leases").filter()

    # #lease_by_code = {l.contract.code: l for l in leases if l.contract and l.contract.code}
    # contracts_dict = {c.code: c for c in contracts if c.code}

    # previous_progress = 0
    # old_obj_count = 0
    # for index,row in df.iterrows():
    #     current_progress = ((index + 1)/len(df))*100

    #     if current_progress - previous_progress >= 1:
    #         previous_progress = current_progress
    #         print(f"{int(current_progress)} %")

    #     obj = (contracts_dict.get(str(row['Kira plani kodu']).replace(".0","")))

    #     if obj:
    #         lease = obj.contract_leases.filter(is_last_project=True).first()
    #         if lease:
    #             old_obj_count += 1
    #             lease.is_title_deed_delivered = True
    #             lease.save()

    # print(f"{old_obj_count} objects updated for leases.")

