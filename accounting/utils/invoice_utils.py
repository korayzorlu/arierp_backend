from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value,F
from django.conf import settings

import pyodbc
import os
import traceback
import pandas as pd
from decimal import Decimal
from datetime import datetime

from accounting.models import *
from common.models import Status
from partners.models import Partner
from common.utils.common_utils import normalize,safe_decimal
from leasing.models import Lease,Contract

def fetch_invoices_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "accounting","sql","faturalar.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        all_leases = Lease.objects.select_related().filter(is_last_project=True)
        all_leases_dict = {l.main_lease_id: l for l in all_leases}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            # 1. codes
            invoice_codes = [r.TrnId for r in records]
            lease_codes = [r.TrnOprLeasingOperationPrjId for r in records]
            partner_codes = [r.CustomerId for r in records]
            # 2. querysets
            invoices = Invoice.objects.select_related().filter(trn_id__in=invoice_codes)
            leases = Lease.objects.select_related().filter(lease_id__in=lease_codes)
            partners = Partner.objects.select_related().filter(crm_code__in=partner_codes)
            # 3. dicts
            invoice_dict = {i.trn_id: i for i in invoices}
            lease_dict = {l.lease_id: l for l in leases}
            partner_dict = {p.crm_code: p for p in partners}
            for index,data in enumerate(records):
                if str(data.TrnId):
                    obj = (invoice_dict.get(str(data.TrnId)))
                else:
                    obj = None

                if obj:
                    if obj.lease.is_last_project:
                        obj.trn_id = str(data.TrnId) or ""
                        obj.lease = lease_dict.get(str(data.TrnOprLeasingOperationPrjId))
                        obj.partner = partner_dict.get(str(data.CustomerId))
                        obj.invoice_no = str(data.InvoiceNumber) or ""
                        obj.type = "sale"
                        obj.date = make_aware(data.InvoiceDate) if data.InvoiceDate else None
                        obj.amount = safe_decimal(data.InvoiceAmount)
                        update_objs.append(obj)
                    else:
                        last_lease = all_leases_dict.get(obj.lease.main_lease_id)
                        last_lease.trn_id = str(data.TrnId) or ""
                        last_lease.lease = lease_dict.get(str(data.TrnOprLeasingOperationPrjId))
                        last_lease.partner = partner_dict.get(str(data.CustomerId))
                        last_lease.invoice_no = str(data.InvoiceNumber) or ""
                        last_lease.type = "sale"
                        last_lease.date = make_aware(data.InvoiceDate) if data.InvoiceDate else None
                        last_lease.amount = safe_decimal(data.InvoiceAmount)
                        update_objs.append(last_lease)
                    # obj.trn_id = str(data.TrnId) or ""
                    # obj.lease = lease_dict.get(str(data.TrnOprLeasingOperationPrjId))
                    # obj.partner = partner_dict.get(str(data.CustomerId))
                    # obj.invoice_no = str(data.InvoiceNumber) or ""
                    # obj.type = "sale"
                    # obj.date = make_aware(data.InvoiceDate) if data.InvoiceDate else None
                    # obj.amount = safe_decimal(data.InvoiceAmount)
                    # update_objs.append(obj)
                    update_progress += 1
                else:
                    lease = lease_dict.get(str(data.TrnOprLeasingOperationPrjId))
                    if lease:
                        if lease.is_last_project:
                            use_lease = lease
                        else:
                            use_lease = all_leases_dict.get(lease.main_lease_id)
                    else:
                        use_lease = None

                    create_objs.append(Invoice(
                        company = company_obj,
                        trn_id = str(data.TrnId) or "",
                        lease = use_lease,
                        #lease = lease,
                        partner = partner_dict.get(str(data.CustomerId)),
                        invoice_no = str(data.InvoiceNumber) or "",
                        type = "sale",
                        date = make_aware(data.InvoiceDate) if data.InvoiceDate else None,
                        amount = safe_decimal(data.InvoiceAmount),
                    ))
                    create_progress += 1
            if update_objs:
                Invoice.objects.bulk_update(update_objs, [
                    "trn_id",
                    "lease",
                    "partner",
                    "invoice_no",
                    "type",
                    "date",
                    "amount",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Invoice.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} fatura güncellendi.")
        print(f"Toplam {create_progress} fatura oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def export_invoices(self):
    objs = Invoice.objects.select_related("lease","partner","lease__currency").prefetch_related().filter()

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()

    data = {
        "İşlem ID": [],
        "Kira Planı": [],
        "Fatura No": [],
        "Tutar": [],
        "PB": [],
        "Tarih": [],
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["İşlem ID"].append(obj.trn_id)
        data["Kira Planı"].append(obj.lease.code or "")
        data["Fatura No"].append(obj.invoice_no or "")
        data["Tutar"].append(obj.amount or Decimal("0.00"))
        data["PB"].append(obj.lease.currency.code or "")
        data["Tarih"].append(obj.date or None)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Tutar",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "accounting", "invoices", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-faturalar.xlsx"
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
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()