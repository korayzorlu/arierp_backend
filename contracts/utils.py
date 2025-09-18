from django.http import JsonResponse
from django.utils.timezone import make_aware

from datetime import datetime
import pandas as pd
import io
import os
import random
import string

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
            
            obj = Contract.objects.create(
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
            obj.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

def export_contract_payments(self):
    objs = ContractPayment.objects.select_related("contract","contract__partner").filter(contract__project = "SİNPAŞ KASABA THERMAL WELLNESS RESORT").order_by("-contract__code")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme": [],
        "Proje": [],
        "Nereden": [],
        "Nereye": [],
        "İşlem Tİpi": [],
        "İşlem Grubu": [],
        "Hesap Kart Kodu": [],
        "Cari Kart Adı": [],
        "İşlem Tarihi": [],
        "Borç": [],
        "Alacak": [],
        "PB": [],
        "Yerel Borç": [],
        "Yerel Alacak": [],
        "Kur(Yerel)": [],
        "Açıklama": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress


        data["Sözleşme"].append(obj.contract.code)
        data["Proje"].append(obj.contract.project if obj.contract else "")
        data["Nereden"].append(obj.trn_from_id or "")
        data["Nereye"].append(obj.type or "")
        data["İşlem Tİpi"].append(obj.posting_type or "")
        data["İşlem Grubu"].append(obj.group_name or "")
        data["Hesap Kart Kodu"].append(obj.account_code or "")
        data["Cari Kart Adı"].append(obj.account_name or "")
        data["İşlem Tarihi"].append(obj.date or "")
        data["Borç"].append(obj.debit_amount)
        data["Alacak"].append(obj.credit_amount)
        data["PB"].append(obj.currency.code if obj.currency else "")
        data["Yerel Borç"].append(obj.local_debit_amount)
        data["Yerel Alacak"].append(obj.local_credit_amount)
        data["Kur(Yerel)"].append(obj.exchange_rate)
        data["Açıklama"].append(obj.description)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Borç",
        "Alacak",
        "Yerel Borç",
        "Yerel Alacak",
        "Kur(Yerel)",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "contracts", "contract_payments", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-tahsilatlar.xlsx"
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