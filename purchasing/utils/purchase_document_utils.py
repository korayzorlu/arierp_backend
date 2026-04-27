from django.conf import settings
from django.utils.timezone import make_aware

import pyodbc
import os
import traceback
import logging

from purchasing.models import *
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner

def fetch_purchase_documents_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "purchasing","sql","satin_alma_belgeleri.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        purchase_documents = PurchaseDocument.objects.select_related().filter(company_id=int(company))
        leases = Lease.objects.select_related().filter(company_id=int(company))
        partners = Partner.objects.select_related().filter(company_id=int(company))
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        purchase_documents_by_code = {p.document_id: p for p in purchase_documents if p.document_id}
        leases_dict = {l.lease_id: l for l in leases}
        partners_dict = {p.crm_code: p for p in partners}
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
                if str(data.DocumentHeaderId):
                    obj = (purchase_documents_by_code.get(str(data.DocumentHeaderId)))
                else:
                    obj = None

                if obj:
                    obj.document_id = str(data.DocumentHeaderId) or ""
                    obj.code = str(data.DocumentHeaderCode) or ""
                    obj.document_number = str(data.DocumentNumber) or ""
                    obj.document_date = make_aware(data.DocumentDate) if data.DocumentDate else None
                    obj.lease = leases_dict.get(str(data.OperationProjectId))
                    obj.partner = partners_dict.get(str(data.CustomerId))
                    obj.vendor = partners_dict.get(str(data.VendorId))
                    obj.amount = safe_decimal(data.LineTotal)
                    obj.vat_amount = safe_decimal(data.VatTotal)
                    obj.total_amount = safe_decimal(data.GeneralTotal)
                    obj.currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode)
                    obj.exchange_rate = safe_decimal(data.ExchangeRate)
                    obj.document_status = str(data.DocumentStatus) or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(PurchaseDocument(
                        company = company_obj,
                        document_id = str(data.DocumentHeaderId) or "",
                        code = str(data.DocumentHeaderCode) or "",
                        document_number = str(data.DocumentNumber) or "",
                        document_date = make_aware(data.DocumentDate) if data.DocumentDate else None,
                        lease = leases_dict.get(str(data.OperationProjectId)),
                        partner = partners_dict.get(str(data.CustomerId)),
                        vendor = partners_dict.get(str(data.VendorId)),
                        amount = safe_decimal(data.LineTotal),
                        vat_amount = safe_decimal(data.VatTotal),
                        total_amount = safe_decimal(data.GeneralTotal),
                        currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode),
                        exchange_rate = safe_decimal(data.ExchangeRate),
                        document_status = str(data.DocumentStatus) or ""
                    ))
                    create_progress += 1
            if update_objs:
                PurchaseDocument.objects.bulk_update(update_objs, [
                    "document_id",
                    "code",
                    "document_number",
                    "document_date",
                    "lease",
                    "partner",
                    "vendor",
                    "amount",
                    "vat_amount",
                    "total_amount",
                    "currency",
                    "exchange_rate",
                    "document_status"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                PurchaseDocument.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        objs_for_delete = PurchaseDocument.objects.select_related().filter(vendor__crm_code__in=["1461", "3374", "3781", "5451", "5785", "7987", "10356", "10506","10681","10682","23670","28814","29447"],company_id=int(company))
        objs_for_delete.delete()
        print(f"Toplam {update_progress} satınalma belgesi güncellendi.")
        print(f"Toplam {create_progress} satınalma belgesi oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)

def fetch_purchase_document_items_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "purchasing","sql","satin_alma_belgesi_satirlari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        purchase_document_items = PurchaseDocumentItem.objects.select_related().filter(company_id=int(company))
        purchase_documents = PurchaseDocument.objects.select_related().filter(company_id=int(company)).only("document_id")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        purchase_document_items_dict = {p.document_line_id: p for p in purchase_document_items if p.document_line_id}
        purchase_documents_dict = {p.document_id: p for p in purchase_documents if p.document_id}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.DocumentHeaderId):
                    obj = (purchase_document_items_dict.get(str(data.DocumentLineId)))
                else:
                    obj = None

                if obj:
                    if purchase_documents_dict.get(str(data.DocumentHeaderId)):
                        obj.document_line_id = str(data.DocumentLineId) or ""
                        obj.c_type_id = str(data.CTypeId) or ""
                        obj.purchase_document = purchase_documents_dict.get(str(data.DocumentHeaderId))
                        obj.stock_name = str(data.StockName) or ""
                        obj.description = str(data.OffsetInfo) or ""
                        obj.quantity = int(data.Quantity) if data.Quantity else 0
                        obj.unit_amount = safe_decimal(data.UnitPrice)
                        obj.amount = safe_decimal(data.TotalPrice)
                        obj.vat_amount = safe_decimal(data.VatTotal)
                        obj.total_amount = safe_decimal(data.GeneralTotal)
                        update_objs.append(obj)
                        update_progress += 1
                else:
                    if purchase_documents_dict.get(str(data.DocumentHeaderId)):
                        create_objs.append(PurchaseDocumentItem(
                            company = company_obj,
                            document_line_id = str(data.DocumentLineId) or "",
                            c_type_id = str(data.CTypeId) or "",
                            purchase_document = purchase_documents_dict.get(str(data.DocumentHeaderId)),
                            stock_name = str(data.StockName) or "",
                            description = str(data.OffsetInfo) or "",
                            quantity = int(data.Quantity) if data.Quantity else 0,
                            unit_amount = safe_decimal(data.UnitPrice),
                            amount = safe_decimal(data.TotalPrice),
                            vat_amount = safe_decimal(data.VatTotal),
                            total_amount = safe_decimal(data.GeneralTotal)
                        ))
                        create_progress += 1
            if update_objs:
                PurchaseDocumentItem.objects.bulk_update(update_objs, [
                    "document_line_id",
                    "c_type_id",
                    "purchase_document",
                    "stock_name",
                    "description",
                    "quantity",
                    "unit_amount",
                    "amount",
                    "vat_amount",
                    "total_amount"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                PurchaseDocumentItem.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} satın alma belgesi satırı güncellendi.")
        print(f"Toplam {create_progress} satın alma belgesi satırı oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)
