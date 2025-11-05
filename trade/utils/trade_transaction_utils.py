from django.conf import settings
from django.utils.timezone import make_aware

import pyodbc
import os
import traceback
import logging
import gc

from common.utils.common_utils import normalize,safe_decimal
from trade.models import *

def fetch_trade_transactions_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "trade","sql","cari_hareketler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        trade_transactions = TradeTransaction.objects.select_related("partner","lease","currency").filter(company__id=int(company))
        partners = Partner.objects.select_related().filter(company__id=int(company))
        leases = Lease.objects.select_related().all()
        currencies = Currency.objects.select_related().all()

        trade_transaction_by_crm = {t.trade_transaction_id: t for t in trade_transactions if t.trade_transaction_id}
        del trade_transactions
        gc.collect()

        partners_dict = {p.crm_code: p for p in partners}
        leases_dict = {l.lease_id: l for l in leases}
        currencies_dict = {c.code: c for c in currencies}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.TrnId):
                    obj = (trade_transaction_by_crm.get(str(data.TrnId)))
                else:
                    obj = None

                if obj:
                    obj.trade_transaction_id = str(data.TrnId) or ""
                    obj.partner = partners_dict.get(str(data.CustomerId))
                    obj.lease = leases_dict.get(str(data.TrnOprLeasingOperationPrjId))
                    obj.posting_group_id = str(data.TrnPostingGroupId) or ""
                    obj.posting_group_name = str(data.JrnStpPstGrpName) or ""
                    obj.description = str(data.TrnDescription) or ""
                    obj.document_no = str(data.TrnReturnDocumentNo) or ""
                    obj.amount_type = str(data.TrnAmountType) or ""
                    obj.due_date = make_aware(data.TrnDueDate) if data.TrnDueDate else None
                    obj.record_date = make_aware(data.TrnCreateDate) if data.TrnCreateDate else None
                    obj.currency = currencies_dict.get("TRY" if data.TrnCurrencyCode == "TL" else data.TrnCurrencyCode)
                    obj.amount = safe_decimal(data.TrnAmount)
                    obj.local_amount = safe_decimal(data.TrnAmountLocal)
                    obj.exchange_rate = safe_decimal(data.TrnExchangeRateLocal)
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(TradeTransaction(
                        company = company_obj,
                        trade_transaction_id = str(data.TrnId) or "",
                        partner = partners_dict.get(str(data.CustomerId)),
                        lease = leases_dict.get(str(data.TrnOprLeasingOperationPrjId)),
                        posting_group_id = str(data.TrnPostingGroupId) or "",
                        posting_group_name = str(data.JrnStpPstGrpName) or "",
                        description = str(data.TrnDescription) or "",
                        document_no = str(data.TrnReturnDocumentNo) or "",
                        amount_type = str(data.TrnAmountType) or "",
                        due_date = make_aware(data.TrnDueDate) if data.TrnDueDate else None,
                        record_date = make_aware(data.TrnCreateDate) if data.TrnCreateDate else None,
                        currency = currencies_dict.get("TRY" if data.TrnCurrencyCode == "TL" else data.TrnCurrencyCode),
                        amount = safe_decimal(data.TrnAmount),
                        local_amount = safe_decimal(data.TrnAmountLocal),
                        exchange_rate = safe_decimal(data.TrnExchangeRateLocal)
                    ))
                    create_progress += 1

            if update_objs:
                TradeTransaction.objects.bulk_update(update_objs, [
                    "trade_transaction_id",
                    "partner",
                    "lease",
                    "posting_group_id",
                    "posting_group_name",
                    "description",
                    "document_no",
                    "amount_type",
                    "due_date",
                    "record_date",
                    "currency",
                    "amount",
                    "local_amount",
                    "exchange_rate"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                TradeTransaction.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        
        del trade_transaction_by_crm
        gc.collect()
        print(f"Toplam {update_progress} cari hesap hareketi güncellendi.")
        print(f"Toplam {create_progress} cari hesap hareketi oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)
