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
from collections import defaultdict

from .models import *

def export_partner_advances(self):
    objs = Partner.objects.select_related().filter(
        Q(advance_amount__gt=0) |
        Q(advance_amount__lt=0)
    ).order_by('advance_amount')

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Müşteri": [],
        "TC/VKN No": [],
        "CRM Kodu": [],
        "TL Bakiye": [],
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Müşteri"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["CRM Kodu"].append(obj.crm_code)
        data["TL Bakiye"].append(obj.advance_amount)

    df = pd.DataFrame(data)
    # df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "operation", "partner_advances", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-müşteri-avansları.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Müşteri Avansları', index=False)
        

    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_partner_advance_activities(self):
    objs = PartnerAdvanceActivityLease.objects.select_related().filter(leaseflex_automation = True).order_by("partner_advance_activity__partner__name","-id")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme No": [],
        "Müşteri": [],
        "TC/VKN No": [],
        "İşlenen Tutar": [],
        "PB": [],
        "İşlem Tarihi": [],
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Sözleşme No"].append(obj.lease.contract.code if obj.lease and obj.lease.contract else "")
        data["Müşteri"].append(obj.partner_advance_activity.partner.name if obj.partner_advance_activity and obj.partner_advance_activity.partner else "")
        data["TC/VKN No"].append(obj.partner_advance_activity.partner.tc_vkn_no if obj.partner_advance_activity and obj.partner_advance_activity.partner else "")
        data["İşlenen Tutar"].append(obj.processed_amount if obj.processed_amount is not None else 0)
        data["PB"].append(obj.partner_advance_activity.currency.code if obj.partner_advance_activity and obj.partner_advance_activity.currency else "")
        data["İşlem Tarihi"].append(datetime.today().strftime("%y%m%d"))

    df = pd.DataFrame(data)
    # df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "operation", "partner_advance_activities", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-müşteri-avansları.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Müşteri Avansları', index=False)
        

    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_title_deed_invoice_controls(self):
    objs = Lease.objects.select_related(
        "contract","contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation"
    ).prefetch_related("lease_invoices","lease_purchase_documents").filter(
        Q(is_last_project=True)
    ).exclude(
        Q(contract__partner__types__contains=['special'])
    ).order_by("-activation_date")

    old_leases = Lease.objects.filter().only('code','main_lease_id').order_by('-lease_id')
    old_leases_dict = defaultdict(list)
    for ol in old_leases:
        old_leases_dict[ol.main_lease_id].append(ol)

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Kira Planı": [],
        "Versiyon Geçmişi": [],
        "Sözleşme": [],
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Satıcı": [],
        "Proje": [],
        "Blok": [],
        "Bağımsız Bölüm": [],
        "Alt Statü": [],
        "Statü": [],
        "Fatura Durumu": [],
        "Satıcı Fatura Durumu": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        old_leases = old_leases_dict.get(obj.main_lease_id, [])

        old_leases_list = []
        for old_lease in old_leases:
            old_leases_list.append(old_lease.code)

        data["Sözleşme"].append(obj.contract.code)
        data["Kira Planı"].append(obj.code)
        data["Versiyon Geçmişi"].append(str(old_leases_list).replace("[","").replace("]","").replace("'",""))
        data["Müşteri İsmi"].append(obj.contract.partner.name if obj.contract.partner else "")
        data["TC/VKN No"].append(obj.contract.partner.tc_vkn_no if obj.contract.partner else "")
        data["Crm Kodu"].append(obj.contract.partner.crm_code if obj.contract.partner else "")
        data["Satıcı"].append(obj.contract.vendor.name if obj.contract.vendor else "")
        data["Proje"].append(obj.contract.project if obj.contract else "")
        data["Blok"].append(obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj.quick_quotation else "" )
        data["Bağımsız Bölüm"].append(obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj.quick_quotation else "")
        data["Alt Statü"].append(obj.status.name if obj.status else "")
        data["Statü"].append(obj.get_lease_status_display())
        data["Fatura Durumu"].append("Kesildi" if obj.lease_invoices.select_related().all().only("id").exists() else "Fatura Yok")
        data["Satıcı Fatura Durumu"].append("Kesildi" if obj.lease_purchase_documents.select_related().all().only("id").exists() else "Fatura Yok")


    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    if "Statü Değişme Tarihi" in df.columns:
        df["Statü Değişme Tarihi"] = pd.to_datetime(df["Statü Değişme Tarihi"]).dt.tz_localize(None)

    numeric_columns = [

    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "operation", "title_deed_invoice_controls", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)



    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-tapu-fatura-kontrol.xlsx"
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