from django.http import JsonResponse
from django.utils.timezone import make_aware

from datetime import datetime
import pandas as pd
import io
from decimal import Decimal

from .models import *
from common.models import Status
from partners.models import Partner

def is_valid_quick_quotation_data(data):
    if not data.get('code') or not data.get('partner'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def is_valid_quotation_data(data):
    if not data.get('code') or not data.get('partner'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

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
                quotation_no = row['Teklif No'],
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
            
            obj = Quotation.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row['Hızlı Teklif No'],
                status = Status.objects.filter(name = str(row["Durum"])).first() or None,
                quick_quotation = QuickQuotation.objects.select_related().filter(quotation_no = str(row["Teklif No"])).first() or None,
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