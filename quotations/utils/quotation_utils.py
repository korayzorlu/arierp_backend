from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.conf import settings

import pyodbc
import os
from datetime import datetime
import pandas as pd
import io
from decimal import Decimal

from quotations.models import *
from common.models import Status
from contracts.models import Contract
from common.utils.common_utils import normalize, safe_decimal

def import_quotations(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = []
        empty_rows = df[required_columns].isnull().any(axis=1)
        if empty_rows.any():
            self.process.status = "rejected"
            self.process.save()
            self.process.delete()
            return

        self.process.status = "in_progress"
        self.process.items_count = len(df)
        self.process.save()
        
        previous_progress = 0
        for index,row in df.iterrows():
            current_progress = ((index + 1)/len(df))*100

            if current_progress - previous_progress >= 5:
                self.process.progress = int(current_progress)
                self.process.save()
                previous_progress = current_progress
            
            #type_list = [item.strip().lower() for item in row["type"].split(",")]

            if Quotation.objects.filter(code = row["Teklif No"]).exists():
                continue

            if row['Talep Tarihi'] and not pd.isna(row['Talep Tarihi']):
                request_date = datetime.fromtimestamp(row['Talep Tarihi'] / 1000)
            else:
                request_date = None

            if row['Revizyon Tarihi'] and not pd.isna(row['Revizyon Tarihi']):
                rev_date = datetime.fromtimestamp(row['Revizyon Tarihi'] / 1000)
            else:
                rev_date = None

            if row['Sözleşme Kodu']:
                contract_code = str(int(row['Sözleşme Kodu'])) if type(row['Sözleşme Kodu']) == float else str(row['Sözleşme Kodu'])
                contract = Contract.objects.select_related("partner").filter(code = contract_code).first()
                if contract:
                    partner = contract.partner
                else:
                    partner = None
            else:
                partner = None

            if row['Teklif No']:
                quotation_code = str(int(row['Teklif No'])) if type(row['Teklif No']) == float else str(row['Teklif No'])
                quick_quotation = QuickQuotation.objects.select_related("partner").filter(quotation_no = quotation_code).first()
            else:
                quick_quotation = None

            obj = Quotation.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row['Teklif No'],
                status = Status.objects.filter(name = str(row["Durum"])).first() or None,
                quick_quotation = quick_quotation,
                partner = partner,
                currency = Currency.objects.select_related().filter(code = "TRY" if row["PB"] == "TL" else row["PB"]).first() or None,
                kbm = Decimal(str(row['KBM']).replace(",",".")) if not pd.isna(row['KBM']) else Decimal(str(0)),
                customer_representative = row['Müş. Temsilcisi'],
                kof = row['KOF No'],
                request_date = request_date,
                rev_date = rev_date,
                supplier = row['Satıcı'],
                project = row['Proje'],
            )
            obj.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()


def fetch_quotations_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "quotations","sql","teklifler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        quotations = Quotation.objects.select_related("status","currency","company").all()
        statuses = Status.objects.select_related().all()
        partners = Partner.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        quotation_by_code = {q.code: q for q in quotations if q.code}
        statuses_dict = {s.name: s for s in statuses}
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
                if str(data.QuotationHeaderId):
                    obj = (quotation_by_code.get(str(data.QuotationHeaderId)))
                else:
                    obj = None

                if obj:
                    obj.code = str(data.QuotationHeaderId) or ""
                    obj.status = statuses_dict.get(normalize(data.SubStatuteDefinition))
                    obj.partner = partners_dict.get(str(data.CustomerId))
                    obj.currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode)
                    obj.kbm = safe_decimal(data.LeasingBaseCost)
                    obj.customer_representative = data.CustomerRepresentative or ""
                    obj.request_date = data.RequestDate.date() if data.RequestDate else None
                    obj.supplier = data.Vendor or ""
                    obj.project = data.Project or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Quotation(
                        company = company_obj,
                        code = str(data.QuotationHeaderId) or "",
                        status = statuses_dict.get(normalize(data.SubStatuteDefinition)),
                        partner = partners_dict.get(str(data.CustomerId)),
                        currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode),
                        kbm = safe_decimal(data.LeasingBaseCost),
                        customer_representative = data.CustomerRepresentative or "",
                        request_date = data.RequestDate.date() if data.RequestDate else None,
                        supplier = data.Vendor or "",
                        project = data.Project or ""
                    ))
                    create_progress += 1

            if update_objs:
                Quotation.objects.bulk_update(update_objs, [
                    "code",
                    "status",
                    "partner",
                    "currency",
                    "kbm",
                    "customer_representative",
                    "request_date",
                    "supplier",
                    "project"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Quotation.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} teklif güncellendi.")
        print(f"Toplam {create_progress} teklif oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)


