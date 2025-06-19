from django.http import JsonResponse
from django.utils.timezone import make_aware

from datetime import datetime
import pandas as pd
import io
from decimal import Decimal

from .models import *
from common.models import Status
from partners.models import Partner

def is_valid_lease_data(data):
    if not data.get('code') or not data.get('lease'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def import_leases(self, df_json):
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

            if Lease.objects.filter(code = row["Kira Planı Kodu"]).exists():
                continue

            LEASE_STATUS_CHOICES = (
                ('aktiflestirildi', ('Aktifleştirildi')),
                ('iptal_edildi', ('İptal Edildi')),
                ('devredildi', ('Devredildi')),
                ('baskasina_transfer_edildi', ('Başkasına Transfer Edildi')),
                ('planlandi', ('Planlandı')),
                ('durduruldu', ('Durduruldu')),
                ('feshedildi', ('Feshedildi')),
                ('revize_edildi', ('Revize Edildi')),
                ('pert', ('Pert')),
                ('envantere_alindi', ('Envantere Alındı')),
                ('para_birimi_degisti', ('Para Birimi Değişti')),
                ('kanuni_takibe_alindi', ('Kanuni Takibe Alındı')),
            )
            display_to_status = {v: k for k, v in LEASE_STATUS_CHOICES}

            if row['Aktifleştirme Tarihi']:
                activation_date = datetime.fromtimestamp(row['Aktifleştirme Tarihi'] / 1000)
            else:
                activation_date = None
            
            obj = Lease.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row['Kira Planı Kodu'],
                contract = Contract.objects.filter(code = str(row["Sözleşme Kodu"])).first() or None,
                type = row['Tipi'],
                vat = Decimal(str(row['KDV Oranı (%)'])),
                activation_date = activation_date,
                lease_status = display_to_status[row['Ana Statü']],
                currency = Currency.objects.select_related().filter(code = "TRY" if row["PB"] == "TL" else row["PB"]).first() or None,
                musteri_baz_maliyet = Decimal(str(row['Müşteri Baz Maliyet']).replace(",",".")),    
                vade =int( row['Peş. Hariç Ödeme Vadesi']),
                leasing_rate = Decimal(str(row['Yıllık Leasing Oranı (%)'])),
                irr = Decimal(str(row['Opr. IRR']).replace(",",".")),
                project_no = row['Proje No'],
                status = Status.objects.select_related().filter(name = row["Alt Statü"]).first() or None,
                leasing_type = row['Kira Planı Türü (Söz./Kesin)'],
                application_no = row['Başvuru No'],
                is_last_project = True if row['IS_LAST_PROJECT'] == 1 else False,
                current_request = row['CurrentRequest'],
                finansman_kurum = row['Finansman Kurum'],
                is_tufe = True if row['Tüfeli Mi?'] == "Evet" else False,
                is_musterek = True if row['Müşterek mi?'] == "Evet" else False,
                bbsn = row['BBSN No'],
            )
            obj.save()

            if row['Vergi/TC Kimlik No']:
                contract = Contract.objects.select_related("partner").filter(code = str(row["Sözleşme Kodu"])).first()
                try:
                    tc_vkn_no = str(int(row['Vergi/TC Kimlik No']))
                except:
                    tc_vkn_no = None
                if contract:
                    contract.partner = Partner.objects.select_related().filter(tc_vkn_no = tc_vkn_no,formal_name = str(row['Müşteri Adı'])).first() or None
                    contract.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()