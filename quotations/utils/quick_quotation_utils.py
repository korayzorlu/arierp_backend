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

def import_quick_quotations(self, df_json):
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

            if QuickQuotation.objects.filter(code = row["Hızlı Teklif No"]).exists():
                continue

            if row['Müşteri İmza Tarihi'] and not pd.isna(row['Müşteri İmza Tarihi']):
                customer_signature_date = datetime.fromtimestamp(row['Müşteri İmza Tarihi'] / 1000)
            else:
                customer_signature_date = None

            if row['Bağımsız Bölüm Teslim Tarihi'] and not pd.isna(row['Bağımsız Bölüm Teslim Tarihi']):
                unit_delivery_date = datetime.fromtimestamp(row['Bağımsız Bölüm Teslim Tarihi'] / 1000)
            else:
                unit_delivery_date = None

            if row['Başlangıç Tarihi'] and not pd.isna(row['Başlangıç Tarihi']):
                start_date = datetime.fromtimestamp(row['Başlangıç Tarihi'] / 1000)
            else:
                start_date = None

            if row['Bitiş Tarihi'] and not pd.isna(row['Bitiş Tarihi']):
                finish_date = datetime.fromtimestamp(row['Bitiş Tarihi'] / 1000)
            else:
                finish_date = None

            if row['Sözleşme Kodu']:
                contract_code = str(int(row['Sözleşme Kodu'])) if type(row['Sözleşme Kodu']) == float else str(row['Sözleşme Kodu'])
                contract = Contract.objects.select_related("partner").filter(code = contract_code).first()
                if contract:
                    partner = contract.partner
                else:
                    partner = None
            else:
                partner = None
            
            obj = QuickQuotation.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row['Hızlı Teklif No'],
                status = Status.objects.filter(name = str(row["Alt Statü"])).first() or None,
                partner = partner,
                quotation_no = str(int(row['Teklif No'])) if type(row['Teklif No']) == float and not pd.isna(row['Teklif No']) else str(row['Teklif No']),
                customer_type = row['Müşteri Tipi'],
                project = row['Proje Adı'],
                block = row['Blok'],
                unit = row['Bağımsız Bölüm No'],
                currency = Currency.objects.select_related().filter(code = "TRY" if row["PB"] == "TL" else row["PB"]).first() or None,
                price = Decimal(str(row['KDV Hariç Tutar']).replace(",",".")) if not pd.isna(row['KDV Hariç Tutar']) else Decimal(str(0)),
                vat = Decimal(str(int(row['KDV'].replace("KDV %","")))) if not pd.isna(row['KDV']) else Decimal(str(0)),
                customer_signature_date = customer_signature_date,   
                unit_delivery_date = unit_delivery_date,
                is_tufe = True if row['Tüfeli Mi?'] == "Evet" else False,
                ortalama_tahsil_suresi = Decimal(str(row['Ortalama Tahsilat Süresi']).replace(",",".")) if not pd.isna(row['Ortalama Tahsilat Süresi']) else Decimal(str(0)),
                devremulk = row['Devremülk Dönemi'],
                start_date = start_date,
                finish_date = finish_date,
                bbsn = row['BBSN No'],
            )
            obj.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

def fetch_quick_quotations_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "quotations","sql","hizli_teklifler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        quick_quotations = QuickQuotation.objects.select_related("status","currency","company").filter(company=int(company))
        partners = Partner.objects.select_related().filter(company=int(company))
        statuses = Status.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        quick_quotation_by_code = {q.code: q for q in quick_quotations if q.code}
        partners_dict = {p.crm_code: p for p in partners if p.crm_code}
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
                if str(data.RPR_QUO_ID):
                    obj = (quick_quotation_by_code.get(str(data.RPR_QUO_ID)))
                else:
                    obj = None

                if obj:
                    obj.code = str(data.RPR_QUO_ID) or ""
                    obj.quotation_no = str(data.QUO_HEADER_ID) or ""
                    obj.partner = partners_dict.get(str(data.CRM_CUSTOMER_ID))
                    obj.project = data.PROJECT_NAME or ""
                    obj.block = data.BLOCK_NO or ""
                    obj.unit = data.FREE_PART_NO or ""
                    obj.status = statuses_dict.get(normalize(data.LAST_SUB_STATU_NAME))
                    obj.currency = currencies_dict.get("TRY" if data.GROSS_SALE_AMOUNT_CURR_ID == "TL" else data.GROSS_SALE_AMOUNT_CURR_ID)
                    obj.price = safe_decimal(data.GROSS_SALE_AMOUNT)
                    obj.vat = safe_decimal(data.KDV.replace("KDV %","") if data.KDV else None)
                    obj.customer_signature_date = data.CUSTOMER_SIGN_DATE.date() if data.CUSTOMER_SIGN_DATE else None
                    obj.unit_delivery_date = data.FREE_PART_DELIVERY_DATE.date() if data.FREE_PART_DELIVERY_DATE else None
                    obj.ortalama_tahsil_suresi = safe_decimal(data.AVERAGE_RETURN_PERIOD)
                    obj.devremulk = data.TIMESHARE_PERIOD or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(QuickQuotation(
                        company = company_obj,
                        code = str(data.RPR_QUO_ID) or "", 
                        quotation_no = str(data.QUO_HEADER_ID) or "",
                        partner = partners_dict.get(str(data.CRM_CUSTOMER_ID)),
                        project = data.PROJECT_NAME or "",
                        block = data.BLOCK_NO or "",
                        unit = data.FREE_PART_NO or "",
                        status = statuses_dict.get(normalize(data.LAST_SUB_STATU_NAME)),
                        currency = currencies_dict.get("TRY" if data.GROSS_SALE_AMOUNT_CURR_ID == "TL" else data.GROSS_SALE_AMOUNT_CURR_ID),
                        price = safe_decimal(data.GROSS_SALE_AMOUNT),
                        vat = safe_decimal(data.KDV.replace("KDV %","")),
                        customer_signature_date = data.CUSTOMER_SIGN_DATE.date() if data.CUSTOMER_SIGN_DATE else None,
                        unit_delivery_date = data.FREE_PART_DELIVERY_DATE.date() if data.FREE_PART_DELIVERY_DATE else None,
                        ortalama_tahsil_suresi = safe_decimal(data.AVERAGE_RETURN_PERIOD),
                        devremulk = data.TIMESHARE_PERIOD or "",
                    ))
                    create_progress += 1

            if update_objs:
                QuickQuotation.objects.bulk_update(update_objs, [
                    "code",
                    "quotation_no",
                    "partner",
                    "project",
                    "block",
                    "unit",
                    "status",
                    "currency",
                    "price",
                    "vat",
                    "customer_signature_date",
                    "unit_delivery_date",
                    "ortalama_tahsil_suresi",
                    "devremulk",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                QuickQuotation.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} hızlı teklif güncellendi.")
        print(f"Toplam {create_progress} hızlı teklif oluşturuldu.")
        print("--------")

        # SQL_QUERY = """
        # SELECT RPR_QUO_ID,
        #     CRM_CUSTOMER_ID
        # FROM RPR_QUO
        # """

        # cursor = conn.cursor()
        # cursor.execute(SQL_QUERY)
        
        # records = cursor.fetchall()

        # external_data=[
        #     {
        #         "RPR_QUO_ID" : r.RPR_QUO_ID,
        #         "CRM_CUSTOMER_ID" : r.CRM_CUSTOMER_ID,
        #     }
        #     for r in records
        # ]

        # quick_quotations = QuickQuotation.objects.select_related().all()
        # partners = Partner.objects.select_related().all()

        # quick_quotation_by_code = {q.code: q for q in quick_quotations if q.code}
        # partners_dict = {p.crm_code: p for p in partners if p.crm_code}

        # previous_progress = 0
        # for index,data in enumerate(external_data):
        #     current_progress = ((index + 1)/len(external_data))*100

        #     if current_progress - previous_progress >= 1:
        #         previous_progress = current_progress
        #         print(f"{int(current_progress)} %")

        #     if str(data["RPR_QUO_ID"]):
        #         obj = (quick_quotation_by_code.get(str(data["RPR_QUO_ID"])))
        #     else:
        #         obj = None

        #     if obj:
        #         obj.partner = partners_dict.get(str(data["CRM_CUSTOMER_ID"]))
        #         obj.save()
        #     else:
        #         print(f"{str(data["RPR_QUO_ID"])} - {data["CRM_CUSTOMER_ID"]}: ")

    except Exception as e:
        print(e)