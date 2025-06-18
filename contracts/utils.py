from django.http import JsonResponse
from django.utils.timezone import make_aware

from datetime import datetime
import pandas as pd
import io

from .models import *
from common.models import Status
from partners.models import Partner

def is_valid_contract_data(data):
    if not data.get('code') or not data.get('partner'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def import_contracts(self, df_json):
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

            if Contract.objects.filter(code = row["Sözleşme Kodu"]).exists():
                continue

            if row['KOFtan Sözleşmeye Aktarım Tar.']:
                kof_tan_sozlesmeye_aktarim_tarihi = datetime.fromtimestamp(row['KOFtan Sözleşmeye Aktarım Tar.'] / 1000)
            else:
                kof_tan_sozlesmeye_aktarim_tarihi = None

            if row['LopOpenDate']:
                lop_open_date = datetime.fromtimestamp(row['LopOpenDate'] / 1000)
            else:
                lop_open_date = None
            
            partner = Contract.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row['Sözleşme Kodu'],
                #partner = None,
                kof = row['KOF No'],
                quotation = row['Teklif No'],
                committe = row['Komite Adı'],
                credit_type = row['Kredi Tipi Adı'],
                customer_representative = row['Müş. Temsilcisi'],
                supplier = row['Satıcı'],
                project = row['Proje'],
                status = Status.objects.filter(name = row["Alt Statü"]).first() or None,
                mkk_tesciline_gonderilecek_mi = True if row['MKK Tesciline Gönderilecek Mi ?'] == "True" else False,
                kof_tan_sozlesmeye_aktarim_tarihi = make_aware(kof_tan_sozlesmeye_aktarim_tarihi),
                lop_open_date = make_aware(lop_open_date),
            )
            partner.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()