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

from ..models import WarningNotice

def export_warning_notices(self):
    objs = WarningNotice.objects.select_related("contract").filter().order_by("service_date")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme": [],
        "Müşteri": [],
        "Tebliğ Tarihi": [],
        "Öngörülen Fesih Tarihi": [],
        "İhtar Borcu": [],
        "Ödenen Tutar": [],
        "Kalan Tutar": [],
        "Durum": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress


        data["Sözleşme"].append(obj.contract.code if obj.contract else "")
        data["Müşteri"].append(obj.contract.partner.name if obj.contract.partner else "")
        data["Tebliğ Tarihi"].append(obj.service_date.strftime("%d.%m.%Y") if obj.service_date else "")
        data["Öngörülen Fesih Tarihi"].append(obj.official_cancellation_date.strftime("%d.%m.%Y") if obj.official_cancellation_date else "")
        data["İhtar Borcu"].append(obj.debit_amount)
        data["Ödenen Tutar"].append(obj.paid)
        data["Kalan Tutar"].append(obj.diff)
        data["Durum"].append(obj.state)


    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    if "Statü Değişme Tarihi" in df.columns:
        df["Statü Değişme Tarihi"] = pd.to_datetime(df["Statü Değişme Tarihi"]).dt.tz_localize(None)

    numeric_columns = [
        "İhtar Borcu",
        "Ödenen Tutar",
        "Kalan Tutar",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "contracts", "warning_notices", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)



    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-ihtarlar.xlsx"
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

