from django.http import JsonResponse
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

import pandas as pd
import os
from datetime import datetime,date,timedelta

from partners.models import Partner
from leasing.utils.common_utils import vendor_filter_for_views

def is_valid_sector_data(data):
    if not data.get('code') or not data.get('name') or not data.get('mainSectorCode') or not data.get('matchCode') or not data.get('kkbmbSectorCode'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def is_valid_partner_data(data):
    if not data.get('name') or not data.get('formalName'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    if not data.get('customer') and not data.get('supplier') and not data.get('shareholder') and not data.get('special'):
        return False, JsonResponse({'message': 'You must select at least one option, either Customer or Supplier or Shareholder!','status':'error'}, status=400)
    return True, None

def get_partner_types(data):
    types = []
    if data.get('customer'):
        types.append("customer")
    if data.get('supplier'):
        types.append("supplier")
    if data.get('shareholder'):
        types.append("shareholder")
    if data.get('special'):
        types.append("special")
    if data.get('pep'):
        types.append("pep")
    return types

def export_partners(self):
    objs = Partner.objects.select_related().filter(
        Q(types__contains=['special'])
    )

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()

    
    
    # data = {
    #     "İsim": [],
    #     "TC/VKN": [],
    #     "CRM Kodu": [],
    #     "Tel": [],
    #     "Email": [],
    #     "Doğum Tarihi": [],
    #     "Doğum Yeri": [],
    # }

    data = {
        "isim": [],
        "tc_vkn_no": [],
        "crm_kodu": [],
        "email": [],
        "tel": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        # data["İsim"].append(obj.name or "")
        # data["TC/VKN"].append(obj.tc_vkn_no if obj.customer_type == "individual" else obj.vat_no or "")
        # data["CRM Kodu"].append(obj.crm_code or "")
        # data["Tel"].append(obj.phone_number or "")
        # data["Email"].append(obj.email or "")
        # data["Doğum Tarihi"].append(obj.birthday.strftime("%d.%m.%Y") if obj.birthday else "")
        # data["Doğum Yeri"].append(obj.birth_place or "")

        
        data["isim"].append(obj.name)
        data["tc_vkn_no"].append(obj.tc_vkn_no if obj.customer_type == "individual" else obj.vat_no)
        data["crm_kodu"].append(obj.crm_code)
        data["email"].append(obj.email)
        data["tel"].append(obj.phone_number)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [

    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "partners", "partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-partner-listesi.xlsx"
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