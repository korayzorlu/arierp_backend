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


def export_third_persons(self):
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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        ba_objs = obj.bank_activities.select_related("finmaks_transaction").all()
        odeme_detay = ""
        if ba_objs.exists():
            for index,ba in enumerate(ba_objs):
                odeme_detay = f"{ba.finmaks_transaction.bank_account.bank_name} - {ba.finmaks_transaction.transaction_date.strftime('%d.%m.%Y %H:%M') if ba.finmaks_transaction.transaction_date else ''} - {ba.finmaks_transaction.explanation_field} - {ba.description}\n"

                if index == 0:
                    status_map = {
                        "pending": "Kontrol Edilecek",
                        "cleared": "Temiz",
                        "flagged": "Yasaklı",
                        "need_document": "Belge Gerekli",
                    }

                    data["Sorgu Tarihi"].append(obj.created_date.strftime("%d.%m.%Y"))
                    data["İsim"].append(obj.name)
                    data["TC/VKN No"].append(obj.tc_vkn_no)
                    data["Ödeme Detayı"].append(odeme_detay)
                    data["Durum"].append(status_map.get(obj.status, obj.status))
                    data["Email Gönderildi mi?"].append("Evet" if obj.is_email_sent else "Hayır")
                    data["Belge"].append("Evet" if obj.third_person_third_person_documents.all().exists() else "Hayır")
                else:
                    data["Sorgu Tarihi"].append("")
                    data["İsim"].append("")
                    data["TC/VKN No"].append("")
                    data["Ödeme Detayı"].append(odeme_detay)
                    data["Durum"].append("")
                    data["Email Gönderildi mi?"].append("")
                    data["Belge"].append("")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    if "Statü Değişme Tarihi" in df.columns:
        df["Statü Değişme Tarihi"] = pd.to_datetime(df["Statü Değişme Tarihi"]).dt.tz_localize(None)

    numeric_columns = [

    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "compliance", "third_persons", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)



    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-ucuncu-kisiler.xlsx"
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