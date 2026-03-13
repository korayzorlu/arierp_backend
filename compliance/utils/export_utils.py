from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value,OuterRef,Subquery

from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
import re
import os
import random
import string
import pytz
import locale

from compliance.models import *
from leasing.models import BankActivity
from common.models import Status
from partners.models import Partner


def export_active_leases(self):
    objs = ThirdPerson.objects.select_related().filter().order_by("-created_date")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sorgu Tarihi": [],
        "İsim": [],
        "TC/VKN No": [],
        "Ödeme Detayı": [],
        "Durum": [],
        "Email Gönderildi mi?": [],
        "Belge": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        ba_objs = obj.bank_activities.all()
        if ba_objs.exists():
            for ba in ba_objs:
                metin += f"Bank Activity: {ba.activity_date} - {ba.amount} - {ba.description}\n"

        data["Teklif"].append(obj.contract.quotation_obj.code if obj.contract.quotation_obj else "")
        data["Sözleşme"].append(obj.contract.code)
        data["Kira Planı"].append(obj.code)
        data["Müşteri İsmi"].append(obj.contract.partner.name if obj.contract.partner else "")
        data["TC/VKN No"].append(obj.contract.partner.tc_vkn_no if obj.contract.partner else "")
        data["Crm Kodu"].append(obj.contract.partner.crm_code if obj.contract.partner else "")
        data["Satıcı"].append(obj.contract.vendor.name if obj.contract.vendor else "")
        data["Proje"].append(obj.contract.project if obj.contract else "")
        data["Blok"].append(obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj.quick_quotation else "" )
        data["Bağımsız Bölüm"].append(obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj.quick_quotation else "")
        data["Alt Statü"].append(obj.status.name if obj.status else "")
        data["Statü"].append(obj.lease_status if obj.lease_status else "")
        data["Statü Değişme Tarihi"].append(obj.lease_status_update_date)


    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    if "Statü Değişme Tarihi" in df.columns:
        df["Statü Değişme Tarihi"] = pd.to_datetime(df["Statü Değişme Tarihi"]).dt.tz_localize(None)

    numeric_columns = [

    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "active_leases", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)



    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-kira-planlari.xlsx"
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