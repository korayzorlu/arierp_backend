import pandas as pd
import os
import string
import random
from datetime import datetime

from risk.models import AmountDebitTransaction
from leasing.models import Lease

def update_risk_summary():
    pass


def export_amount_debit_transactions(self):
    objs = AmountDebitTransaction.objects.select_related().filter().order_by("-lease__code","id")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    

    data = {
        "Hesap Adı": [],
        "Söz.No": [],
        "Transfer Kodu": [],
        "Kira Planı Statüsü": [],
        "KPYS Alt Statüsü": [],
        "İşlem Grubu": [],
        "PB": [],
        "Tarih": [],
        "İşlem Tipi": [],
        "Borç": [],
        "Alacak": [],
        "Gerçek Bakiye": [],
        "Tem. Bazlı Bky": [],
        "Gün": [],
        "Adat": [],
        "Oran": [],
        "Temerrüt (Vergisiz)": [],
        "Hesaplanan Gecikme Faizi Tutarı (KDV Dahil)": [],
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Hesap Adı"].append(obj.lease.contract.partner.name if obj.lease.contract.partner else "")
        data["Söz.No"].append(obj.lease.code or "")
        data["Transfer Kodu"].append("")
        data["Kira Planı Statüsü"].append("")
        data["KPYS Alt Statüsü"].append("")
        data["İşlem Grubu"].append(obj.process_group)
        data["PB"].append(obj.lease.currency.code if obj.lease.currency else "")
        data["Tarih"].append(obj.due_date.strftime("%d.%m.%Y"))
        data["İşlem Tipi"].append(obj.process_type)
        data["Borç"].append(obj.debit_amount)
        data["Alacak"].append(obj.credit_amount)
        data["Gerçek Bakiye"].append(obj.real_amount)
        data["Tem. Bazlı Bky"].append(obj.for_default_amount)
        data["Gün"].append(obj.day)
        data["Adat"].append(obj.adat_amount)
        data["Oran"].append(obj.interest_rate)
        data["Temerrüt (Vergisiz)"].append(obj.default_amount)
        data["Hesaplanan Gecikme Faizi Tutarı (KDV Dahil)"].append(obj.overdue_interest_rate)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Borç",
        "Alacak",
        "Gerçek Bakiye",
        "Tem. Bazlı Bky",
        "Adat",
        "Oran",
        "Temerrüt (Vergisiz)",
        "Hesaplanan Gecikme Faizi Tutarı (KDV Dahil)",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "risk", "amount_debit_transaction", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-bakiye-temerrut-raporu.xlsx"
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