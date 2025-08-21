from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import Q
from django.utils.timezone import make_aware

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict

from .models import *
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner

@shared_task()
def fetch_purchase_payments(company):
    excel_file = pd.ExcelFile("files/satici-odemeleri.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/satici-odemeleri.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    purchase_payments = PurchasePayment.objects.select_related().all()
    purchase_payments.delete()
    leases = Lease.objects.select_related().exclude(lease_status = 'iptal_edildi')

    purchase_payment_by_code = {l.lease.code: l for l in purchase_payments if l.lease.code}
    leases_dict = {l.code: l for l in leases if l.code}
    
    company_obj = Company.objects.select_related().filter(id=int(company)).first()

    previous_progress = 0
    old_obj_count = 0
    new_obj_count = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        obj = (purchase_payment_by_code.get(str(row['Kira Planı Kodu'])))

        # obj = Lease.objects.select_related().filter(
        #     Q(code=str(row['Kira Planı'])) &
        #     (
        #         Q(lease_status='aktiflestirildi') |
        #         Q(lease_status='planlandi') |
        #         Q(lease_status='durduruldu')
        #     )
        # ).first()
        if obj:
            old_obj_count += 1
            obj.lease = leases_dict.get(str(row["Kira Planı Kodu"]))
            obj.total_contract_amount = Decimal(str(row['Toplam Sözleşme Bedeli (İlk Sözleşme)'])) if not pd.isna(row['Toplam Sözleşme Bedeli (İlk Sözleşme)']) else Decimal("0.00")
            obj.total_vendor_payment = Decimal(str(row['Satıcı Ödemeleri Toplam Tutarı'])) if not pd.isna(row['Satıcı Ödemeleri Toplam Tutarı']) else Decimal("0.00")
            obj.before_total_payment = Decimal(str(row['Ödeme Toplam Öncesi'])) if not pd.isna(row['Ödeme Toplam Öncesi']) else Decimal("0.00")
            obj.after_total_payment = Decimal(str(row['Toplam Ödeme Sonrası'])) if not pd.isna(row['Toplam Ödeme Sonrası']) else Decimal("0.00")
            obj.managing_expense = Decimal(str(row['Yönetim Gideri (Kdv Dahil)'])) if not pd.isna(row['Yönetim Gideri (Kdv Dahil)']) else Decimal("0.00")
            obj.lease_payment_amount =Decimal(str(row['Kira Tahsilat Tutarı'])) if not pd.isna(row['Kira Tahsilat Tutarı']) else Decimal("0.00")
            obj.vendor_payment_with_report_date = Decimal(str(row['Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı'])) if not pd.isna(row['Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı']) else Decimal("0.00")
            obj.next_payment = Decimal(str(row['Sonraki Ödeme'])) if not pd.isna(row['Sonraki Ödeme']) else Decimal("0.00")
            obj.purchasing = int(row['satinalma']) if not pd.isna(row['satinalma']) else 0
            obj.save()
        else:
            new_obj_count += 1
            PurchasePayment.objects.create(
                company=company_obj,
                lease = leases_dict.get(str(row["Kira Planı Kodu"])),
                total_contract_amount = Decimal(str(row['Toplam Sözleşme Bedeli (İlk Sözleşme)'])) if not pd.isna(row['Toplam Sözleşme Bedeli (İlk Sözleşme)']) else Decimal("0.00"),
                total_vendor_payment = Decimal(str(row['Satıcı Ödemeleri Toplam Tutarı'])) if not pd.isna(row['Satıcı Ödemeleri Toplam Tutarı']) else Decimal("0.00"),
                before_total_payment = Decimal(str(row['Ödeme Toplam Öncesi'])) if not pd.isna(row['Ödeme Toplam Öncesi']) else Decimal("0.00"),
                after_total_payment = Decimal(str(row['Toplam Ödeme Sonrası'])) if not pd.isna(row['Toplam Ödeme Sonrası']) else Decimal("0.00"),
                managing_expense = Decimal(str(row['Yönetim Gideri (Kdv Dahil)'])) if not pd.isna(row['Yönetim Gideri (Kdv Dahil)']) else Decimal("0.00"),
                lease_payment_amount =Decimal(str(row['Kira Tahsilat Tutarı'])) if not pd.isna(row['Kira Tahsilat Tutarı']) else Decimal("0.00"),
                vendor_payment_with_report_date = Decimal(str(row['Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı'])) if not pd.isna(row['Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı']) else Decimal("0.00"),
                next_payment = Decimal(str(row['Sonraki Ödeme'])) if not pd.isna(row['Sonraki Ödeme']) else Decimal("0.00"),
                purchasing = int(row['satinalma']) if not pd.isna(row['satinalma']) else 0
            )

    print(f"{new_obj_count} objects created and {old_obj_count} objects updated for leases.")


@shared_task()
def fetch_purchase_documents(company):
    SERVER = "192.168.82.31,1433"
    DATABASE = "ARI_LEASING"
    USERNAME = "lflex"
    PASSWORD = "S!gma2014"

    connectionString = f'''
        DRIVER={{ODBC Driver 18 for SQL Server}};
        SERVER={SERVER};
        DATABASE={DATABASE};
        UID={USERNAME};
        PWD={PASSWORD};
        Provider=SQLNCLI11;
        Integrated Security=SSPI;
        Persist Security Info=False;
        Initial Catalog=MASTER;
        TrustServerCertificate=yes;
    '''

    try:
        conn = pyodbc.connect(connectionString)
        
        SQL_QUERY = """
        SELECT 
            DocumentHeaderId,
            DocumentHeaderCode,
            CustomerId,
            VendorId,
            DocumentNumber,
            DocumentDate,
            CurrencyCode,
            ExchangeRate,
            LineTotal,
            VatTotal,
            GeneralTotal,
            DocumentStatus,
            OperationProjectId
        FROM LeasePurchaseDocumentHeaderList
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "DocumentHeaderId" : r.DocumentHeaderId,
                "DocumentHeaderCode" : r.DocumentHeaderCode,
                "CustomerId" : r.CustomerId,
                "VendorId" : r.VendorId,
                "DocumentNumber" : r.DocumentNumber,
                "DocumentDate" : r.DocumentDate,
                "CurrencyCode" : r.CurrencyCode,
                "ExchangeRate" : r.ExchangeRate,
                "LineTotal" : r.LineTotal,
                "VatTotal" : r.VatTotal,
                "GeneralTotal" : r.GeneralTotal,
                "DocumentStatus" : r.DocumentStatus,
                "OperationProjectId" : r.OperationProjectId
            }
            for r in records
        ]

        purchase_documents = PurchaseDocument.objects.select_related().all()
        leases = Lease.objects.select_related().all()
        partners = Partner.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        purchase_documents_by_code = {p.document_id: p for p in purchase_documents if p.document_id}
        leases_dict = {l.lease_id: l for l in leases}
        partners_dict = {p.crm_code: p for p in partners}
        currencies_dict = {c.code: c for c in currencies}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["DocumentHeaderId"]):
                obj = (purchase_documents_by_code.get(str(data["DocumentHeaderId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.document_id = str(data["DocumentHeaderId"]) or ""
                obj.code = str(data["DocumentHeaderCode"]) or ""
                obj.document_number = str(data["DocumentNumber"]) or ""
                obj.document_date = make_aware(data["DocumentDate"]) if data["DocumentDate"] else None
                obj.lease = leases_dict.get(str(data["OperationProjectId"]))
                obj.partner = partners_dict.get(str(data["CustomerId"]))
                obj.vendor = partners_dict.get(str(data["VendorId"]))
                obj.amount = safe_decimal(data["LineTotal"])
                obj.vat_amount = safe_decimal(data["VatTotal"])
                obj.total_amount = safe_decimal(data["GeneralTotal"])
                obj.currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"])
                obj.exchange_rate = safe_decimal(data["ExchangeRate"])
                obj.document_status = str(data["DocumentStatus"]) or ""
                obj.save()
            else:
                new_obj_count += 1
                PurchaseDocument.objects.create(
                    company = company_obj,
                    document_id = str(data["DocumentHeaderId"]) or "",
                    code = str(data["DocumentHeaderCode"]) or "",
                    document_number = str(data["DocumentNumber"]) or "",
                    document_date = make_aware(data["DocumentDate"]) if data["DocumentDate"] else None,
                    lease = leases_dict.get(str(data["OperationProjectId"])),
                    partner = partners_dict.get(str(data["CustomerId"])),
                    vendor = partners_dict.get(str(data["VendorId"])),
                    amount = safe_decimal(data["LineTotal"]),
                    vat_amount = safe_decimal(data["VatTotal"]),
                    total_amount = safe_decimal(data["GeneralTotal"]),
                    currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"]),
                    exchange_rate = safe_decimal(data["ExchangeRate"]),
                    document_status = str(data["DocumentStatus"]) or ""
                )
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")
    except Exception as e:
        print(e)
