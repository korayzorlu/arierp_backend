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

from leasing.models import *
from common.models import Status
from partners.models import Partner
from .common_utils import *

def translate_third_person_status(status):
    if status == "clear":
        return "Temiz"
    elif status == "pending":
        return ""
    elif status == "flagged":
        return "Yasaklı"
    elif status == "need_document":
        return "Belge/Kimlik Bekleniyor"
    else:
        return ""

def export_bank_activities(self):
    bank_activities = BankActivity.objects.select_related().filter(created_date__date = date.today(), is_vpos = False).order_by("id")
    objs = BankActivityLease.objects.select_related().filter(leaseflex_automation = True).order_by("bank_activity__bank_code","bank_activity__tc_vkn_no")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Hesap Numarası": [],
        "İşlem Tarihi": [],
        "İşlem Kodu": [],
        "Borç / Alacak": [],
        "Döviz kodu": [],
        "Tutar": [],
        "Kontrat No": [],
        "Açıklama": [],
        "Gönderen Ünvanı": [],
        "Gönderen İsmi": [],
        "Gönderen TCKN / VKN": [],
        "3. Şahıs Ödemesi": [],
        "3. Şahıs Durumu": [],
        "Karşı Banka": [],
        "Karşı Şube": [],
        "Karşı Hesap": []
    }

    previous_progress = 0
    for index,bank_activity in enumerate(bank_activities):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        ba_leases = bank_activity.bank_activity_bank_acitivity_leases.filter(leaseflex_automation = True)

        if ba_leases:
            for ba_lease in ba_leases:
                if ba_lease.lease.currency:
                    if ba_lease.lease.currency.code == "TRY":
                        currency = "YTL"
                    else:
                        currency = ba_lease.lease.currency.code
                else:
                    currency = ""

                data["Hesap Numarası"].append(ba_lease.bank_activity.bank_account_no)
                data["İşlem Tarihi"].append(ba_lease.bank_activity.process_date_date.strftime("%y%m%d"))
                data["İşlem Kodu"].append(ba_lease.bank_activity.process_code)
                data["Borç / Alacak"].append(ba_lease.bank_activity.credit_or_debit)
                data["Döviz kodu"].append(currency)
                data["Tutar"].append(float(ba_lease.processed_amount) if ba_lease.processed_amount is not None else None)
                data["Kontrat No"].append(ba_lease.bank_activity.kontrat_no)
                data["Açıklama"].append(ba_lease.bank_activity.description)
                data["Gönderen Ünvanı"].append(ba_lease.lease.contract.code)
                data["Gönderen İsmi"].append(ba_lease.lease.contract.partner.name)
                data["Gönderen TCKN / VKN"].append(ba_lease.bank_activity.tc_vkn_no)
                data["3. Şahıs Ödemesi"].append("Evet" if ba_lease.bank_activity.is_third_person else "")
                data["3. Şahıs Durumu"].append(translate_third_person_status(ba_lease.bank_activity.third_person_status))
                data["Karşı Banka"].append(ba_lease.bank_activity.cross_bank_code)
                data["Karşı Şube"].append(ba_lease.bank_activity.cross_bank_branch_code)
                data["Karşı Hesap"].append(ba_lease.bank_activity.cross_bank_account_no)
        else:
            data["Hesap Numarası"].append(bank_activity.bank_account_no)
            data["İşlem Tarihi"].append(bank_activity.process_date_date.strftime("%y%m%d"))
            data["İşlem Kodu"].append(bank_activity.process_code)
            data["Borç / Alacak"].append(bank_activity.credit_or_debit)
            data["Döviz kodu"].append(bank_activity.currency.code if bank_activity.currency else "")
            data["Tutar"].append(float(bank_activity.amount))
            data["Kontrat No"].append(bank_activity.kontrat_no)
            data["Açıklama"].append(bank_activity.description)
            data["Gönderen Ünvanı"].append("")
            data["Gönderen İsmi"].append("")
            data["Gönderen TCKN / VKN"].append(bank_activity.tc_vkn_no)
            data["3. Şahıs Ödemesi"].append("Evet" if bank_activity.is_third_person else "")
            data["3. Şahıs Durumu"].append(translate_third_person_status(bank_activity.third_person_status))
            data["Karşı Banka"].append(bank_activity.cross_bank_code)
            data["Karşı Şube"].append(bank_activity.cross_bank_branch_code)
            data["Karşı Hesap"].append(bank_activity.cross_bank_account_no)

    # previous_progress = 0
    # for index,obj in enumerate(objs):
    #     current_progress = ((index + 1)/len(objs))*100

    #     if current_progress - previous_progress >= 5:
    #         self.process.progress = int(current_progress)
    #         self.process.save()
    #         previous_progress = current_progress
        
        
    #     #bank_activity_leases = lease.lease_bank_acitivity_leases.filter(leaseflex_automation = True)
    #     if obj.lease.currency:
    #         if obj.lease.currency.code == "TRY":
    #             currency = "YTL"
    #         else:
    #             currency = obj.lease.currency.code
    #     else:
    #         currency = ""
        
    #     data["Hesap Numarası"].append(obj.bank_activity.bank_account_no)
    #     data["İşlem Tarihi"].append(obj.bank_activity.process_date_date.strftime("%y%m%d"))
    #     data["İşlem Kodu"].append(obj.bank_activity.process_code)
    #     data["Borç / Alacak"].append(obj.bank_activity.credit_or_debit)
    #     data["Döviz kodu"].append(currency)
    #     data["Tutar"].append(float(obj.processed_amount) if obj.processed_amount is not None else None)
    #     data["Kontrat No"].append(obj.bank_activity.kontrat_no)
    #     data["Açıklama"].append(obj.bank_activity.description)
    #     data["Gönderen Ünvanı"].append(obj.lease.contract.code)
    #     data["Gönderen İsmi"].append(obj.lease.contract.partner.name)
    #     data["Gönderen TCKN / VKN"].append(obj.bank_activity.tc_vkn_no)
    #     data["3. Şahıs Ödemesi"].append("Evet" if obj.is_third_person else "")
    #     data["Karşı Banka"].append(obj.bank_activity.cross_bank_code)
    #     data["Karşı Şube"].append(obj.bank_activity.cross_bank_branch_code)
    #     data["Karşı Hesap"].append(obj.bank_activity.cross_bank_account_no)

    df = pd.DataFrame(data)
    # df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "bank_activities", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-banka-hareketleri.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Banka Hareketleri', index=False)
        

    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_today_partners(self):
    today = date.today()

    # Get the latest sequency for each lease
    latest_sequency_subquery = Installment.objects.filter(
        lease=OuterRef('pk')
    ).values('lease').annotate(
        max_sequency=Max('sequency')
    ).values('max_sequency')
        
    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__lease_installments__payment_date=today) &
        ~Q(partner_contracts__contract_leases__lease_installments__sequency=Subquery(latest_sequency_subquery))
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days')
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    ).order_by('-max_overdue_days')

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Tel": [],
        "Email": [],
        "Metin": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        #metin = f"Bilgilendirme: Sinpaş Kızılbük projesi’ne ait {today.strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatır, iyi günler dileriz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        metin = f"Değerli müşterimiz, {project_text(self.params)} projesinde bulunan sözleşmelerinizin ödemelerini hatırlatmak isteriz.{"Ödemelerinizi aşağıda linki bulunan online sistemden kontrol edip ödeme yapabilirsiniz." if self.params.get('project') != 'sinpas' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. {"https://odeme.arileasing.com.tr/online-islemler//login.aspx  " if self.params.get('project') != 'sinpas' else ""}Arı Finansal Kiralama(İletişim: 02123102721 / rig@arileasing.com.tr)Mernis No: 0147005285500018"

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
        data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05357750255")
    data["Email"].append("")
    data["Metin"].append(metin)
    
    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05332260858")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05456227095")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05548919220")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05413831801")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05534565457")
    data["Email"].append("")
    data["Metin"].append(metin)
    
    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "today_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-bugün-ödemesi-olanlar.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()


def export_tomorrow_partners(self):
    tomorrow = date.today() + timedelta(days=1)

    # Get the latest sequency for each lease
    latest_sequency_subquery = Installment.objects.filter(
        lease=OuterRef('pk')
    ).values('lease').annotate(
        max_sequency=Max('sequency')
    ).values('max_sequency')

    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__lease_installments__payment_date=tomorrow) &
        ~Q(partner_contracts__contract_leases__lease_installments__sequency=Subquery(latest_sequency_subquery))
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days')
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    ).order_by('-max_overdue_days')

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Tel": [],
        "Email": [],
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
        
        #metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne  ait {tomorrow.strftime('%d.%m.%Y')} tarihli taksit ödemeniz yaklaşmaktadır. Ödeme gününü hatırlatır, iyi günler dileriz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        metin = f"Değerli müşterimiz, {project_text(self.params)} projesinde bulunan sözleşmelerinizin {tomorrow.strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatmak isteriz.{"Ödemelerinizi aşağıda linki bulunan online sistemden kontrol edip ödeme yapabilirsiniz." if self.params.get('project') != 'sinpas' else ""}ÖDEME YAPILDIYSA MESAJI DİKKATE ALMAYINIZ. {"https://odeme.arileasing.com.tr/online-islemler//login.aspx  " if self.params.get('project') != 'sinpas' else ""}Arı Finansal Kiralama(İletişim: 02123102721 / rig@arileasing.com.tr)Mernis No: 0147005285500018"
        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
        data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05357750255")
    data["Email"].append("")
    data["Metin"].append(metin)
    
    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05332260858")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05456227095")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05548919220")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05413831801")
    data["Email"].append("")
    data["Metin"].append(metin)

    data["Müşteri İsmi"].append("")
    data["TC/VKN No"].append("")
    data["Crm Kodu"].append("")
    data["Tel"].append("05534565457")
    data["Email"].append("")
    data["Metin"].append(metin)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "tomorrow_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-yarın-ödemesi-olanlar.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_kdv_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=True) &
        Q(partner_contracts__contract_leases__overdue_amount__gt=100)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    )

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Tel": [],
        "Email": []
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "kdv_risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-kdv-farkı-uygulananlar.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_to_terminated_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        (
            Q(partner_contracts__contract_warning_notices__state='Yeni') |
            Q(partner_contracts__contract_warning_notices__state='Geçerli')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False) &
        Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=datetime.today()) &
        Q(partner_contracts__contract_leases__overdue_days__gt=30) &
        Q(partner_contracts__contract_leases__overdue_amount__gt=1000)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        warning_notice_count=Count(
            'partner_contracts__contract_warning_notices',
            distinct=True,
            filter=Q(partner_contracts__contract_warning_notices__state__in=['Yeni', 'Geçerli'])
        ),
        overdue_check=Case(
            When(
                customer_type='individual',
                then=Case(
                    When(partner_contracts__contract_leases__overdue_days__gt=60, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            When(
                customer_type='institutional',
                then=Case(
                    When(partner_contracts__contract_leases__overdue_days__gt=90, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    )

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
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_kdv_diff=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today()) &
            Q(overdue_days__gt=30) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count(
                'contract__contract_warning_notices',
                distinct=True,
                filter=Q(contract__contract_warning_notices__state__in=['Yeni', 'Geçerli'])
            ),
            overdue_check=Case(
                When(
                    contract__partner__customer_type='individual',
                    then=Case(
                        When(overdue_days__gt=60, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    contract__partner__customer_type='institutional',
                    then=Case(
                        When(overdue_days__gt=90, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).order_by("contract__code","-activation_date").exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )

        total_overdue_amount = Decimal("0")
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount
        
            metin = f"Değerli müşterimiz, {project_text(self.params)} projesi’ne ait {format_currency_tr(total_overdue_amount)} TL ihtar bakiyeniz bulunmaktadır. Fesih sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
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
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "to_terminated_risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-fesih-edilecekler.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_deposite_partners(self):
    objs = Partner.objects.select_related().filter(
        vendor_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__paid__lte=10000) &
        Q(partner_contracts__contract_leases__paid__gte=1000) &
        Q(partner_contracts__contract_leases__overdue_days__gt=0) &
        Q(partner_contracts__contract_leases__overdue_amount__gt=100)
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    )

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme No": [],
        "Kira Planı": [],
        "Müşteri İsmi": [],
        "Müşteri TC": [],
        "Müşteri CRM Kodu": []
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
            Q(contract__partner = obj) &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).order_by("-id")

        total_overdue_amount = Decimal("0")
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount

                data["Sözleşme No"].append(lease.contract.code)
                data["Kira Planı"].append(lease.code)
                data["Müşteri İsmi"].append(lease.contract.partner.name)
                data["Müşteri TC"].append(lease.contract.partner.tc_vkn_no)
                data["Müşteri CRM Kodu"].append(lease.contract.partner.crm_code)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "deposite_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-kaporalar.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_delivery_confirms(self):
    objs = Partner.objects.select_related().filter(
        project_filter_for_views(self.params) &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False) &
        Q(partner_contracts__contract_leases__paid_rate__gte=30) &
        Q(partner_contracts__contract_leases__overdue_amount=0)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    )

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Proje": [],
        "Kira Planı": [],
        "Sözleşme No": [],
        "Tahsilat Oranı": [],
        "Gecikmiş Bakiye": [],
        "Diğer Gecikmiş Bakiye": [],
        "Temerrüt": [],
        "Para Birimi": [],
        "Blok": [],
        "Bağımsız Bölüm": [],
        "Müşteri İsmi": [],
        "Müşteri TC": [],
        "Müşteri Tel": [],
        "Müşteri CRM Kodu": []
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
            project_filter_for_serializers(self.params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(paid_rate__gte=30) &
            Q(overdue_amount=0)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).order_by("contract__code","-activation_date").distinct("contract__code")

        excluded_leases = Lease.objects.select_related("contract__partner").filter(
            Q(contract__partner = obj) &
            project_filter_for_serializers(self.params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        ).exclude(
            id__in=leases.values_list('id', flat=True)
        ).aggregate(total_overdue_amount=Sum('overdue_amount'))

        

        total_overdue_amount = Decimal("0")
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount

                amount_debits = lease.lease_amount_debits.all()

                total_lease_temerrut_amount = Decimal("0")
                for amount_debit in amount_debits:
                    total_lease_temerrut_amount += amount_debit.overdue_interest_rate
                
                data["Proje"].append(lease.contract.project)
                data["Kira Planı"].append(lease.code)
                data["Sözleşme No"].append(lease.contract.code)
                data["Tahsilat Oranı"].append(lease.paid_rate)
                data["Gecikmiş Bakiye"].append(lease.overdue_amount)
                data["Diğer Gecikmiş Bakiye"].append(excluded_leases["total_overdue_amount"] if excluded_leases["total_overdue_amount"] else 0)
                data["Temerrüt"].append(total_lease_temerrut_amount)
                data["Para Birimi"].append(lease.currency.code)
                data["Blok"].append(lease.contract.quotation_obj.quick_quotation.block if lease.contract.quotation_obj and lease.contract.quotation_obj.quick_quotation else "")
                data["Bağımsız Bölüm"].append(lease.contract.quotation_obj.quick_quotation.unit if lease.contract.quotation_obj and lease.contract.quotation_obj.quick_quotation else "")
                data["Müşteri İsmi"].append(lease.contract.partner.name)
                data["Müşteri TC"].append(lease.contract.partner.tc_vkn_no)
                data["Müşteri Tel"].append(lease.contract.partner.phone_number)
                data["Müşteri CRM Kodu"].append(lease.contract.partner.crm_code)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Tahsilat Oranı",
        "Gecikmiş Bakiye",
        "Diğer Gecikmiş Bakiye",
        "Temerrüt",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "delivery_confirms", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-teslim-onay.xlsx"
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

def export_active_leases(self):
    objs = Lease.objects.select_related("contract","contract__partner","contract__quotation_obj__quick_quotation").filter(
        # status_filter_for_leases(self.params) &
        # Q(is_last_project=True)
        Q(is_last_project_arinet=True) &
        Q(real_estate__isnull=True)
    ).order_by("-signature_date")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Teklif": [],
        "Sözleşme": [],
        "Kira Planı": [],
        "Müşteri İsmi": [],
        "TC/VKN No": [],
        "Crm Kodu": [],
        "Satıcı": [],
        "Proje": [],
        "Blok": [],
        "Bağımsız Bölüm": [],
        "RBlok": [],
        "RBağımsız Bölüm": [],
        "BBSN": [],
        "Alt Statü": [],
        "Statü": [],
        "Statü Değişme Tarihi": []
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress


        data["Teklif"].append(obj.contract.quotation_obj.code if obj.contract.quotation_obj else "")
        data["Sözleşme"].append(obj.contract.code)
        data["Kira Planı"].append(obj.code)
        data["Müşteri İsmi"].append(obj.contract.partner.name if obj.contract.partner else "")
        data["TC/VKN No"].append(obj.contract.partner.tc_vkn_no if obj.contract.partner else "")
        data["Crm Kodu"].append(obj.contract.partner.crm_code if obj.contract.partner else "")
        data["Satıcı"].append(obj.contract.vendor.name if obj.contract.vendor else "")
        data["Proje"].append(obj.item.stock_name if obj.item else "")
        data["Blok"].append(obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj.quick_quotation else "" )
        data["Bağımsız Bölüm"].append(obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj.quick_quotation else "")
        data["RBlok"].append(obj.real_estate.block if obj.real_estate else "" )
        data["RBağımsız Bölüm"].append(obj.real_estate.unit if obj.real_estate else "")
        data["BBSN"].append(obj.ari_bbsn if obj.ari_bbsn else "")
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

