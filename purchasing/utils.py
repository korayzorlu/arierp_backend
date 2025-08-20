from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

from datetime import datetime,date,timedelta
import pandas as pd
import os
from decimal import Decimal

from .models import PurchasePayment,PurchaseDocument

def export_purchase_payments(self):
    objs = PurchasePayment.objects.select_related("lease","lease__contract","lease__contract__partner").all()

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
        "Toplam Fatura Tutarı": [],
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

        if obj.lease:
            diff = obj.lease_payment_amount - obj.before_total_payment
            temerrut = obj.lease_payment_amount - obj.before_total_payment
            if (obj.lease_payment_amount - obj.before_total_payment) <= 0:
                talimat = obj.vendor_payment_with_report_date
            else:
                talimat = obj.before_total_payment - obj.managing_expense - obj.total_vendor_payment
            
            purchase_documents = PurchaseDocument.objects.select_related().filter(lease = obj.lease).aggregate(total_total_amount=Sum('total_amount'))

            data["Sözleşme No"].append(obj.lease.contract.code or "")
            data["Kira Planı"].append(obj.lease.code or "")
            data["Müşteri"].append(obj.lease.contract.partner.name if obj.lease.contract.partner else "")
            data["PB"].append(obj.lease.currency.code or "")
            data["Satıcı"].append(obj.lease.contract.vendor.name if obj.lease.contract.vendor else "")
            data["Proje"].append(obj.lease.contract.project or "")
            data["Akticasyon Tarihi"].append(obj.lease.activation_date or "")
            data["Sözleşme Tarihi"].append("")
            data["Ana Statü"].append(obj.lease.lease_status or "")
            data["Alt Statü"].append(obj.lease.status or "")
            data["KDV (%)"].append(obj.lease.vat or Decimal("0.00"))
            data["Toplam Sözleşme Bedeli"].append(obj.total_contract_amount)
            data["Ödeme Toplam Öncesi"].append(obj.before_total_payment)
            data["Toplam Ödeme Sonrası"].append(obj.after_total_payment)
            data["Yönetim Gideri (KDV Dahil)"].append(obj.managing_expense)
            data["Kira Tahsilat Tutarı"].append(obj.lease_payment_amount)
            data["Satıcı Ödemeleri Toplam Tutarı"].append(obj.total_vendor_payment)
            data["Talimat"].append(talimat)
            data["Fark"].append(diff)
            data["Temerrüt"].append(temerrut)
            data["Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı"].append(obj.vendor_payment_with_report_date)
            data["Sonraki Ödeme"].append(obj.next_payment)
            data["Satın Alma"].append(obj.purchasing)
            data["BBSN"].append(obj.lease.bbsn)
            data["Toplam Fatura Tutarı"].append(purchase_documents['total_total_amount'])
            data["Tüfeli mi?"].append("Evet" if obj.lease.is_tufe else "")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "KDV (%)",
        "Toplam Sözleşme Bedeli",
        "Ödeme Toplam Öncesi",
        "Toplam Ödeme Sonrası",
        "Yönetim Gideri (KDV Dahil)",
        "Kira Tahsilat Tutarı",
        "Satıcı Ödemeleri Toplam Tutarı",
        "Talimat",
        "Fark",
        "Temerrüt",
        "Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı",
        "Toplam Fatura Tutarı"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "purchasing", "purchase_payments", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-satici-odemeleri.xlsx"
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