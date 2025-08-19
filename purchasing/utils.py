from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

from datetime import datetime,date,timedelta
import pandas as pd
import os

from .models import PurchasePayment

def export_purchase_payments(self):
    objs = PurchasePayment.objects.select_related("lease","contract").all()

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()

    
    
    data = {
        "Sözleşme No": [],
        "Kira Planı": [],
        "Müşteri": [],
        "PB": [],
        "Satıcı": [],
        "Proje": [],
        "Akticasyon Tarihi": [],
        "Sözleşme Tarihi": [],
        "Ana Statü": [],
        "Alt Statü": [],
        "KDV (%)": [],
        "Toplam Sözleşme Bedeli": [],
        "Ödeme Toplam Öncesi": [],
        "Toplam Ödeme Sonrası": [],
        "Yönetim Gideri (KDV Dahil)": [],
        "Kira Tahsilat Tutarı": [],
        "Satıcı Ödemeleri Toplam Tutarı": [],
        "Talimat": [],
        "Fark": [],
        "Temerrüt": [],
        "Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı": [],
        "Sonraki Ödeme": [],
        "Satın Alma": [],
        "BBSN": [],
        "Tüfeli mi?": []
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        diff = obj.lease_payment_amount - obj.before_total_payment
        temerrut = obj.lease_payment_amount - obj.before_total_payment
        if (obj.lease_payment_amount - obj.before_total_payment) <= 0:
            talimat = obj.vendor_payment_with_report_date
        else:
            talimat = obj.before_total_payment - obj.managing_expense - obj.total_vendor_payment

        data["Sözleşme No"].append(obj.lease.contract__code or "")
        data["Kira Planı"].append(obj.lease.code or "")
        data["Müşteri"].append(obj.lease.contract.partner.name or "")
        data["PB"].append(obj.lease.currency.code or "")
        data["Satıcı"].append(obj.lease.contract.currency.code or "")
        data["Proje"].append(obj.lease.contract.project or "")
        data["Akticasyon Tarihi"].append(obj.lease.activation_date or "")
        data["Sözleşme Tarihi"].append("")
        data["Ana Statü"].append(obj.lease.lease_status or "")
        data["Alt Statü"].append(obj.lease.status or "")
        data["KDV (%)"].append()
        data["Toplam Sözleşme Bedeli"].append()
        data["Ödeme Toplam Öncesi"].append()
        data["Toplam Ödeme Sonrası"].append()
        data["Yönetim Gideri (KDV Dahil)"].append()
        data["Kira Tahsilat Tutarı"].append()
        data["Satıcı Ödemeleri Toplam Tutarı"].append()
        data["Talimat"].append()
        data["Fark"].append()
        data["Temerrüt"].append()
        data["Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı"].append()
        data["Sonraki Ödeme"].append()
        data["Satın Alma"].append()
        data["BBSN"].append()
        data["Tüfeli mi?"].append()

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "purchasing", "purchase_payments", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-satici-odemeleri.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()