from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

from datetime import datetime,date,timedelta
import pandas as pd
import os
from decimal import Decimal

from purchasing.models import PurchasePayment,PurchaseDocument
from leasing.models import Lease
from collections import defaultdict

def export_purchase_payments(self):
    if self.params.get('project'):
        objs = PurchasePayment.objects.select_related("lease","lease__contract","lease__contract__partner").filter(
            Q(lease__contract__partner__types__contains=['special']) |
            Q(lease__contract__partner__crm_code__in=["23371", "9341", "10495", "4305", "10437", "4441", "11722", "24120"])
        )
    else:
        objs = PurchasePayment.objects.select_related("lease","lease__contract","lease__contract__partner").filter(
            ~Q(lease__contract__partner__types__contains=['special']) &
            ~Q(lease__contract__partner__crm_code__in=["23371", "9341", "10495", "4305", "10437", "4441", "11722", "24120"]) 
        )

    old_leases = Lease.objects.filter().only('code','main_lease_id').order_by('-lease_id')
    old_leases_dict = defaultdict(list)
    for ol in old_leases:
        old_leases_dict[ol.main_lease_id].append(ol)

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()

    data = {
        "Sözleşme No": [],
        "Kira Planı": [],
        "Müşteri": [],
        "PB": [],
        "Satıcı": [],
        "CRM Satıcı": [],
        "Proje": [],
        "Akticasyon Tarihi": [],
        "Sözleşme Tarihi": [],
        "Ana Statü": [],
        "Alt Statü": [],
        "KDV (%)": [],
        "Toplam Sözleşme Bedeli": [],
        "KDV Farkı Uygulanmış Sözleşme Bedeli": [],
        "Ödeme Toplam Öncesi": [],
        "Toplam Ödeme Sonrası": [],
        "Yönetim Gideri (KDV Dahil)": [],
        "Kira Tahsilat Tutarı": [],
        "Satıcı Ödemeleri Toplam Tutarı": [],
        "IFS Tahsilat Tutarı": [],
        "Talimat": [],
        "Fark": [],
        "Temerrüt": [],
        "Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı": [],
        "Sonraki Ödeme": [],
        "Satın Alma": [],
        "BBSN": [],
        "Satıcı Fatura Tutarı": [],
        "Fatura PB": [],
        "IFS Fatura Tutarı": [],
        "IFS Fatura PB": [],
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
            
            pds = obj.lease.lease_purchase_documents.all().aggregate(total_total_amount=Sum('total_amount'))

            old_leases = old_leases_dict.get(obj.lease.main_lease_id, [])

            old_leases_list = []
            for old_lease in old_leases:
                old_leases_list.append(old_lease)

            purchase_documents_exist = any(lease.lease_purchase_documents.exists() for lease in old_leases_list)

            pd_currency = ""
            if purchase_documents_exist:
                for lease in old_leases_list:
                    purchase_documents = lease.lease_purchase_documents.all()
                    if purchase_documents.exists():
                        pd_currency = purchase_documents.first().currency.code if purchase_documents.first().currency else ""

            #kdv farkı
            if obj.lease.activation_date and obj.lease.activation_date >= date(2023, 7, 10) and (obj.lease.vat == Decimal('18.00') or obj.lease.vat == Decimal('8.00')):
                installments = obj.lease.lease_installments.select_related().filter(
                    Q(lease__activation_date__gte=date(2023, 7, 10)) &
                    (
                        Q(lease__vat=Decimal('18.00')) |
                        Q(lease__vat=Decimal('8.00'))
                    )
                ).order_by('sequency')

                kdv_rate = Decimal('1.18') if obj.lease.vat == Decimal('18.00') else Decimal('1.08')
                kdv_new_rate = Decimal('1.2') if obj.lease.vat == Decimal('18.00') else Decimal('1.1')

                if installments:
                    max_sequency = installments.aggregate(max_seq=Max('sequency'))['max_seq']
                    installments = installments.exclude(sequency=max_sequency)
                    installments_total = installments.select_related().filter().aggregate(
                        total_amount=Sum('amount')
                    )

                    updated_amount = (installments_total['total_amount']/kdv_rate)*kdv_new_rate if installments_total['total_amount'] else Decimal('0.00')
                else:
                    updated_amount = (obj.total_contract_amount/kdv_rate)*kdv_new_rate
            else:
                updated_amount = Decimal('0.00')

            data["Sözleşme No"].append(obj.lease.contract.code or "")
            data["Kira Planı"].append(obj.lease.code or "")
            data["Müşteri"].append(obj.lease.contract.partner.name if obj.lease.contract.partner else "")
            data["PB"].append(obj.lease.currency.code or "")
            data["Satıcı"].append(obj.lease.contract.vendor.name if obj.lease.contract.vendor else "")
            data["CRM Satıcı"].append(obj.lease.crm_satici if obj.lease.crm_satici else "")
            data["Proje"].append(obj.lease.contract.project or "")
            data["Akticasyon Tarihi"].append(obj.lease.activation_date.strftime("%d.%m.%Y") if obj.lease.activation_date else "")
            data["Sözleşme Tarihi"].append(obj.lease.signature_date.strftime("%d.%m.%Y") if obj.lease.signature_date else "")
            data["Ana Statü"].append(obj.lease.lease_status or "")
            data["Alt Statü"].append(obj.lease.status or "")
            data["KDV (%)"].append(obj.lease.vat or Decimal("0.00"))
            data["Toplam Sözleşme Bedeli"].append(obj.total_contract_amount)
            data["KDV Farkı Uygulanmış Sözleşme Bedeli"].append(updated_amount)
            data["Ödeme Toplam Öncesi"].append(obj.before_total_payment)
            data["Toplam Ödeme Sonrası"].append(obj.after_total_payment)
            data["Yönetim Gideri (KDV Dahil)"].append(obj.managing_expense)
            data["Kira Tahsilat Tutarı"].append(obj.lease_payment_amount)
            data["Satıcı Ödemeleri Toplam Tutarı"].append(obj.total_vendor_payment)
            data["IFS Tahsilat Tutarı"].append(obj.lease.ifs_tahsilat or Decimal("0.00"))
            data["Talimat"].append(talimat)
            data["Fark"].append(diff)
            data["Temerrüt"].append(temerrut)
            data["Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı"].append(obj.vendor_payment_with_report_date)
            data["Sonraki Ödeme"].append(obj.next_payment)
            data["Satın Alma"].append(obj.purchasing)
            data["BBSN"].append(obj.lease.ari_bbsn)
            data["Satıcı Fatura Tutarı"].append(pds['total_total_amount'] if pds['total_total_amount'] and pds['total_total_amount'] > 0 else "")
            data["Fatura PB"].append(pd_currency)
            data["IFS Fatura Tutarı"].append(obj.lease.crm_invoice_total_amount if obj.lease.crm_invoice_total_amount else "")
            data["IFS Fatura PB"].append("TRY" if obj.lease.crm_invoice_total_amount else "")
            data["Tüfeli mi?"].append("Evet" if obj.lease.is_tufe else "")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "KDV (%)",
        "Toplam Sözleşme Bedeli",
        "KDV Farkı Uygulanmış Sözleşme Bedeli",
        "Ödeme Toplam Öncesi",
        "Toplam Ödeme Sonrası",
        "Yönetim Gideri (KDV Dahil)",
        "Kira Tahsilat Tutarı",
        "Satıcı Ödemeleri Toplam Tutarı",
        "IFS Tahsilat Tutarı",
        "Talimat",
        "Fark",
        "Temerrüt",
        "Rapor Tarihi İtibariyle Ödenecek Satıcı Tutarı",
        "Satıcı Fatura Tutarı",
        "IFS Fatura Tutarı",
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

def export_purchase_documents(self):
    objs = PurchaseDocument.objects.select_related("lease","lease__contract","lease__contract__partner","lease__contract__vendor","lease__currency").filter()

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme No": [],
        "Kira Planı": [],
        "Müşteri": [],
        "Satıcı": [],
        "CRM satıcı": [],
        "BBSN": [],
        "Döküman No": [],
        "Döküman Tarihi": [],
        "Toplam Tutar": [],
        "KDV Toplam": [],
        "Genel Toplam": [],
        "PB": [],
        "IFS'ten Gelen Tutar": [],
        "IFS'ten Gelen Tutar PB": [],
        "Kur": [],
        "Statü": [],
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Sözleşme No"].append(obj.lease.contract.code if obj.lease and obj.lease.contract else "")
        data["Kira Planı"].append(obj.lease.code if obj.lease else "")
        data["Müşteri"].append(obj.lease.contract.partner.name if obj.lease and obj.lease.contract and obj.lease.contract.partner else "")
        data["Satıcı"].append(obj.lease.contract.vendor.name if obj.lease and obj.lease.contract and obj.lease.contract.vendor else "")
        data["CRM satıcı"].append(obj.lease.crm_satici if obj.lease and obj.lease.crm_satici else "")
        data["BBSN"].append(obj.lease.bbsn if obj.lease else "")
        data["Döküman No"].append(obj.document_number or "")
        data["Döküman Tarihi"].append(obj.document_date or "")
        data["Toplam Tutar"].append(obj.amount)
        data["KDV Toplam"].append(obj.vat_amount)
        data["Genel Toplam"].append(obj.total_amount)
        data["PB"].append(obj.currency.code if obj.currency else "")
        data["IFS'ten Gelen Tutar"].append(obj.lease.crm_invoice_total_amount if obj.lease and obj.lease.crm_invoice_total_amount else Decimal("0.00"))
        data["IFS'ten Gelen Tutar PB"].append("TRY")
        data["Kur"].append(obj.exchange_rate)
        data["Statü"].append(obj.document_status or "")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Toplam Tutar",
        "KDV Toplam",
        "Genel Toplam",
        "Kur",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "purchasing", "purchase_documents", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-satin-alma-belgeleri.xlsx"
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