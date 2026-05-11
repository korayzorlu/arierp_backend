import pandas as pd
import os
import string
import random
from datetime import datetime
from decimal import Decimal
from docxtpl import DocxTemplate
from django.conf import settings

from risk.models import AmountDebitTransaction
from leasing.models import Lease
from leasing.utils.lease_utils import check_risk_status,get_future_payments
from contracts.models import WarningNotice
from companies.models import Company

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


def set_risk_status(company, batch_size=1000):
    objs = Lease.objects.select_related().filter(company=int(company), is_last_project = True)

    update_progress = 0
    updated_objects = []
    for obj in objs:
        obj.risk_status = check_risk_status(obj)

        update_progress += 1
        updated_objects.append(obj)

        if len(updated_objects) >= batch_size:
            Lease.objects.bulk_update(updated_objects, ['risk_status'])
            updated_objects = []

    if updated_objects:
        Lease.objects.bulk_update(updated_objects, ['risk_status'])

    print(f"Toplam {update_progress} kira planı risk durumu güncellendi.")
    print("--------")

def set_warning_notice_files(company,reset):
    objs = WarningNotice.objects.select_related().filter(state__in=['Yeni', 'Geçerli'], company=int(company))
    leases = Lease.objects.select_related().filter(company=int(company), is_last_project = True)
    leases_dict = {lease.contract.uuid: lease for lease in leases if lease.contract}

    company_obj = Company.objects.select_related().filter(id=int(company)).first()

    update_progress = 0
    for obj in objs:
        lease = leases_dict.get(obj.contract.uuid)
        if lease:
            file_name = lease.contract.code.replace("/","-")
            doc = DocxTemplate(f"files/gecikme-ihtari-{'kep' if lease.contract.partner.kep else 'noter'}.docx")

            if not reset:
                file_path = os.path.join(settings.BASE_DIR, "media", "docs", str(company_obj.uuid), "risk", "warned_risk_partners", "documents",f"{file_name}.docx")  
                if os.path.exists(file_path):
                    continue
    
            def format_currency(value):
                return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")
            
            if lease.contract.partner.is_commercial:
                if lease.contract.partner.tc_vkn_no and len(lease.contract.partner.tc_vkn_no) > 0:
                    tc_vkn_no = lease.contract.partner.tc_vkn_no
                elif lease.contract.partner.vat_no and len(lease.contract.partner.vat_no) > 0:
                    tc_vkn_no = lease.contract.partner.vat_no
                else:
                    tc_vkn_no = ''
            else:
                tc_vkn_no = lease.contract.partner.tc_vkn_no if lease.contract.partner.tc_vkn_no else ''

            gecikme_bakiye = lease.overdue_amount
            masraf_bakiye = (gecikme_bakiye / Decimal('100')) * Decimal('10')
            toplam_borc_bakiye = gecikme_bakiye + masraf_bakiye
            gelecek_bakiye = get_future_payments(lease.lease_id)
            toplam_bakiye = toplam_borc_bakiye + gelecek_bakiye

            context = {
                "tarih": datetime.today().strftime('%d.%m.%Y'),
                "isim": lease.contract.partner.name,
                "tc_vkn_no": tc_vkn_no,
                "adres": lease.contract.partner.address,
                "sozlesme_tarih": lease.activation_date.strftime('%d.%m.%Y') if lease.activation_date else '',
                "sozlesme_no": lease.contract.code,
                "il": f"{lease.city} ili, " if lease.city else '',
                "ilce": f"{lease.district} ilçesi, " if lease.district else '',
                "ada": f"{lease.island} ada, " if lease.island else '',
                "parsel": f"{lease.parcel} parsel, " if lease.parcel else '',
                "blok": f"{lease.block} blok, " if lease.block else '',
                "bagimsiz_bolum": f"{lease.unit} numaralı bağımsız bölüm " if lease.unit else '',
                "gecikme_bakiye": format_currency(gecikme_bakiye),
                "masraf_bakiye": format_currency(masraf_bakiye),
                "toplam_borc_bakiye": format_currency(toplam_borc_bakiye),
                "gelecek_bakiye": format_currency(gelecek_bakiye),
                "toplam_bakiye": format_currency(toplam_bakiye),
            }
            doc.render(context)

            files_path = os.path.join(settings.BASE_DIR, "media", "docs", str(company_obj.uuid), "risk", "warned_risk_partners", "documents",f"{file_name}.docx")
            doc.save(files_path)

        update_progress += 1

    print(f"Toplam {update_progress} ihtar dosyası oluşturuldu.")
    print("--------")
