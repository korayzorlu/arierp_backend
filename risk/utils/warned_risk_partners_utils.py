from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
import re
import os
import random
import string

from leasing.models import Lease
from partners.models import Partner

from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr

def export_warned_risk_partners_for_sms(self):
    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False) &
        Q(partner_contracts__contract_leases__overdue_days__gt=30) &
        Q(partner_contracts__contract_leases__overdue_amount__gt=1000)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
        overdue_check=Case(
            When(
                customer_type='individual',
                then=Case(
                    When(partner_contracts__contract_leases__overdue_days__lte=60, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            When(
                customer_type='institutional',
                then=Case(
                    When(partner_contracts__contract_leases__overdue_days__lte=90, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    ).filter(warning_notice_count__gt=0,overdue_check=True)

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Tel": [],
        "Email": [],
        "Tutar": [],
        "Metin": []
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(self.params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(contract__currency__code="TRY") &
            Q(is_kdv_diff=False) &
            Q(overdue_days__gt=30) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
            When(
                contract__partner__customer_type='individual',
                then=Case(
                    When(overdue_days__lte=60, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            When(
                contract__partner__customer_type='institutional',
                then=Case(
                    When(overdue_days__lte=90, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            default=Value(False),
            output_field=BooleanField()
        )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )

        total_overdue_amount = Decimal("0")
        max_overdue_days = 0
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount
                if lease.overdue_days > max_overdue_days:
                    max_overdue_days = lease.overdue_days
            if max_overdue_days > 0:
                overdue_start_date = date.today() - timedelta(days=max_overdue_days)
        
            metin = f"Değerli müşterimiz, {project_text(self.params)} projesi’ne ait {overdue_start_date.strftime("%d.%m.%Y")} son ödeme tarihli {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        else:
             metin = ""

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
        data["Tutar"].append(total_overdue_amount)
        data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05357750255")
    data["Email"].append("")
    data["Tutar"].append(total_overdue_amount)
    data["Metin"].append(metin)
    
    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05332260858")
    data["Email"].append("")
    data["Tutar"].append(total_overdue_amount)
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05456227095")
    data["Email"].append("")
    data["Tutar"].append(total_overdue_amount)
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05548919220")
    data["Email"].append("")
    data["Tutar"].append(total_overdue_amount)
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05413831801")
    data["Email"].append("")
    data["Tutar"].append(total_overdue_amount)
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05534565457")
    data["Email"].append("")
    data["Tutar"].append(total_overdue_amount)
    data["Metin"].append(metin)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "risk", "warned_risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler-sms.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_warned_risk_partners(self):
    objs = Lease.objects.select_related("contract","contract__partner","contract__quotation_obj__quick_quotation").filter(
        vendor_filter_for_serializers(self.params) &
        (
            Q(lease_status='aktiflestirildi') |
            Q(lease_status='planlandi') |
            Q(lease_status='durduruldu')
        ) &
        Q(is_last_project=True) &
        Q(is_kdv_diff=False) &
        Q(is_credit=False) &
        Q(overdue_days__gt=30) &
        Q(overdue_amount__gt=1000)
    ).annotate(
        warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
    ).filter(warning_notice_count__gt=0)

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme": [],
        "Kira Planı": [],
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Satıcı": [],
        "Proje": [],
        "Blok": [],
        "Bağımsız Bölüm": [],
        "Kdv Dahil Kira Toplamı": [],
        "Tahsilat Tutarı": [],
        "0-30": [],
        "31-60": [],
        "61-90": [],
        "91-120": [],
        "121-150": [],
        "151-180": [],
        "181 >": [],
        "Gecikme Tutarı": [],
        "PB": [],
        "Gecikme Gün": [],
        "Tahsilat Oranı (%)": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Sözleşme"].append(obj.contract.code)
        data["Kira Planı"].append(obj.code)
        data["Müşteri İsmi"].append(obj.contract.partner.name if obj.contract.partner else "")
        data["TC/VKN No"].append(obj.contract.partner.tc_vkn_no if obj.contract.partner else "")
        data["Crm Kodu"].append(obj.contract.partner.crm_code if obj.contract.partner else "")
        data["Satıcı"].append(obj.contract.vendor.name if obj.contract.vendor else "")
        data["Proje"].append(obj.contract.project if obj.contract else "")
        data["Blok"].append(obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj.quick_quotation else "" )
        data["Bağımsız Bölüm"].append(obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj.quick_quotation else "")
        data["Kdv Dahil Kira Toplamı"].append(obj.total_payment)
        data["Tahsilat Tutarı"].append(obj.paid)
        data["0-30"].append(obj.overdue_0_30)
        data["31-60"].append(obj.overdue_31_60)
        data["61-90"].append(obj.overdue_61_90)
        data["91-120"].append(obj.overdue_91_120)
        data["121-150"].append(obj.overdue_121_150)
        data["151-180"].append(obj.overdue_151_180)
        data["181 >"].append(obj.overdue_181_gte)
        data["Gecikme Tutarı"].append(obj.overdue_amount)
        data["PB"].append(obj.currency.code)
        data["Gecikme Gün"].append(obj.overdue_days)
        data["Tahsilat Oranı (%)"].append(obj.paid_rate)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Kdv Dahil Kira Toplamı",
        "Tahsilat Tutarı",
        "0-30",
        "31-60",
        "61-90",
        "91-120",
        "121-150",
        "151-180",
        "181 >",
        "Gecikme Tutarı",
        "Tahsilat Oranı (%)",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "risk", "warned_risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx"
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
