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
import pytz
import locale

from .models import *
from common.models import Status
from partners.models import Partner

def is_valid_lease_data(data):
    if not data.get('code') or not data.get('lease'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def is_valid_installment_data(data):
    if not data.get('code') or not data.get('installment'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def get_lease_status_value(display_label):
    LEASE_STATUS_CHOICES = (
        ('aktiflestirildi', ('Aktifleştirildi')),
        ('iptal_edildi', ('İptal Edildi')),
        ('devredildi', ('Devredildi')),
        ('baskasina_transfer_edildi', ('Başkasına Transfer Edildi')),
        ('planlandi', ('Planlandı')),
        ('durduruldu', ('Durduruldu')),
        ('feshedildi', ('Feshedildi')),
        ('revize_edildi', ('Revize Edildi')),
        ('pert', ('Pert')),
        ('envantere_alindi', ('Envantere Alındı')),
        ('para_birimi_degisti', ('Para Birimi Değişti')),
        ('kanuni_takibe_alindi', ('Kanuni Takibe Alındı')),
    )
    
    for value, label in LEASE_STATUS_CHOICES:
        if label == display_label:
            return value
    return None

def format_currency_tr(value):
    try:
        # Sayıya çevirmeye çalış
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        value = Decimal(value).quantize(Decimal("0.01"))

        # Binlik ve ondalık ayracı formatla
        parts = f"{value:,.2f}".split(".")
        integer_part = parts[0].replace(",", ".")
        decimal_part = parts[1]
        return f"{integer_part},{decimal_part}"
    except (InvalidOperation, ValueError, TypeError):
        # Hatalı değer gelirse boş string döndür
        return ""


def extract_contract_numbers(description):
    # Parantez içindeki tüm numaraları yakalar
    matches = re.findall(r'sözleşme.*?\(?(\d{4,})[-–]?(\d{0,})\)?', description.lower())
    contract_numbers = []
    for match in matches:
        contract_numbers.append(match[0])
        if match[1]:
            contract_numbers.append(match[1])
    return contract_numbers


def import_leases(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = []
        empty_rows = df[required_columns].isnull().any(axis=1)
        if empty_rows.any():
            self.process.status = "rejected"
            self.process.save()
            self.process.delete()
            return

        self.process.status = "in_progress"
        self.process.items_count = len(df)
        self.process.save()
        
        previous_progress = 0
        for index,row in df.iterrows():
            current_progress = ((index + 1)/len(df))*100

            if current_progress - previous_progress >= 5:
                self.process.progress = int(current_progress)
                self.process.save()
                previous_progress = current_progress
            
            #type_list = [item.strip().lower() for item in row["type"].split(",")]
            """
            if Lease.objects.filter(code = row["Kira Planı Kodu"]).exists():
                continue

            LEASE_STATUS_CHOICES = (
                ('aktiflestirildi', ('Aktifleştirildi')),
                ('iptal_edildi', ('İptal Edildi')),
                ('devredildi', ('Devredildi')),
                ('baskasina_transfer_edildi', ('Başkasına Transfer Edildi')),
                ('planlandi', ('Planlandı')),
                ('durduruldu', ('Durduruldu')),
                ('feshedildi', ('Feshedildi')),
                ('revize_edildi', ('Revize Edildi')),
                ('pert', ('Pert')),
                ('envantere_alindi', ('Envantere Alındı')),
                ('para_birimi_degisti', ('Para Birimi Değişti')),
                ('kanuni_takibe_alindi', ('Kanuni Takibe Alındı')),
            )
            display_to_status = {v: k for k, v in LEASE_STATUS_CHOICES}

            if row['Aktifleştirme Tarihi']:
                activation_date = datetime.fromtimestamp(row['Aktifleştirme Tarihi'] / 1000)
            else:
                activation_date = None
            
            obj = Lease.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row['Kira Planı Kodu'],
                contract = Contract.objects.filter(code = str(row["Sözleşme Kodu"])).first() or None,
                type = row['Tipi'],
                vat = Decimal(str(row['KDV Oranı (%)'])),
                activation_date = activation_date,
                lease_status = display_to_status[row['Ana Statü']],
                currency = Currency.objects.select_related().filter(code = "TRY" if row["PB"] == "TL" else row["PB"]).first() or None,
                musteri_baz_maliyet = Decimal(str(row['Müşteri Baz Maliyet']).replace(",",".")),    
                vade =int( row['Peş. Hariç Ödeme Vadesi']),
                leasing_rate = Decimal(str(row['Yıllık Leasing Oranı (%)'])),
                irr = Decimal(str(row['Opr. IRR']).replace(",",".")),
                project_no = row['Proje No'],
                status = Status.objects.select_related().filter(name = row["Alt Statü"]).first() or None,
                leasing_type = row['Kira Planı Türü (Söz./Kesin)'],
                application_no = row['Başvuru No'],
                is_last_project = True if row['IS_LAST_PROJECT'] == 1 else False,
                current_request = row['CurrentRequest'],
                finansman_kurum = row['Finansman Kurum'],
                is_tufe = True if row['Tüfeli Mi?'] == "Evet" else False,
                is_musterek = True if row['Müşterek mi?'] == "Evet" else False,
                bbsn = row['BBSN No'],
            )
            obj.save()
            """

            if row["Sözleşme Kodu"]:
                if type(row["Sözleşme Kodu"]) == float:
                    contract_code = str(int(row["Sözleşme Kodu"]))
                else:
                    contract_code = str(row["Sözleşme Kodu"])
                contract = Contract.objects.select_related("partner").filter(code = contract_code).first()
                if contract:
                    contract.partner = Partner.objects.select_related().filter(crm_code = str(int(row['Müşteri']))).first() or None
                    contract.save()

                    if not contract.partner:
                        if row['Vergi/TC Kimlik No']:
                            contract = Contract.objects.select_related("partner").filter(code = str(row["Sözleşme Kodu"])).first()
                            try:
                                tc_vkn_no = str(int(row['Vergi/TC Kimlik No']))
                            except:
                                tc_vkn_no = None
                            if contract:
                                contract.partner = Partner.objects.select_related().filter(tc_vkn_no = tc_vkn_no,formal_name = str(row['Müşteri Adı'])).first() or None
                                contract.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

def import_installments(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = []
        empty_rows = df[required_columns].isnull().any(axis=1)
        if empty_rows.any():
            self.process.status = "rejected"
            self.process.save()
            self.process.delete()
            return

        self.process.status = "in_progress"
        self.process.items_count = len(df)
        self.process.save()
        
        previous_progress = 0
        for index,row in df.iterrows():
            current_progress = ((index + 1)/len(df))*100

            if current_progress - previous_progress >= 5:
                self.process.progress = int(current_progress)
                self.process.save()
                previous_progress = current_progress

            if Installment.objects.select_related().filter(lease__code = str(row["Kira Planı Kodu"]), sequency = int(row["Kira Planı Sıra No"])).exists():
                continue

            if row['Ödeme Tarihi']:
                payment_date = datetime.fromtimestamp(row['Ödeme Tarihi'] / 1000)
            else:
                payment_date = None
            
            obj = Installment.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                lease = Lease.objects.select_related().filter(code = str(row["Kira Planı Kodu"])).first() or None,
                payment_date = payment_date,
                vat = Decimal(str(row['Vergi Oranı']).replace(",",".")) if not pd.isna(row['Vergi Oranı']) else Decimal(str(0)),
                amount = Decimal(str(row['Taksit']).replace(",",".")) if not pd.isna(row['Taksit']) else Decimal(str(0)),
                paid = Decimal(str(row['Toplam Ödeme Tutarı']).replace(",",".")) if not pd.isna(row['Toplam Ödeme Tutarı']) else Decimal(str(0)),
                principal = Decimal(str(row['Ana Para']).replace(",",".")) if not pd.isna(row['Ana Para']) else Decimal(str(0)),
                interest = Decimal(str(row['Faiz']).replace(",",".")) if not pd.isna(row['Faiz']) else Decimal(str(0)),
                sequency = int(row['Kira Planı Sıra No']) if not pd.isna(row['Kira Planı Sıra No']) else int(0),
            )
            obj.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

def import_bank_activities(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        df = df[df["Tutar"].apply(lambda x: float(str(x).replace(",", ".")) >= 0)]
        
        required_columns = []
        empty_rows = df[required_columns].isnull().any(axis=1)
        if empty_rows.any():
            self.process.status = "rejected"
            self.process.save()
            self.process.delete()
            return

        self.process.status = "in_progress"
        self.process.items_count = len(df)
        self.process.save()
        
        current_bank_activities = BankActivity.objects.select_related().filter()
        if current_bank_activities:
            for current_bank_activity in current_bank_activities:
                current_bank_activity.delete()

        current_leases = Lease.objects.select_related().filter(leaseflex_automation = True)
        for current_lease in current_leases:
            current_lease.leaseflex_automation = False
            current_lease.processed_amount = Decimal("0")
            current_lease.save()

        bank_activity_leases = BankActivity.objects.select_related().filter()
        for bank_activity_lease in bank_activity_leases:
            bank_activity_lease.delete()
        
        previous_progress = 0
        for index,row in df.iterrows():
            current_progress = ((index + 1)/len(df))*100

            if current_progress - previous_progress >= 5:
                self.process.progress = int(current_progress)
                self.process.save()
                previous_progress = current_progress

            if row['İşlem Tarihi']:
                process_date = make_aware(datetime.strptime(str(row['İşlem Tarihi']), "%y%m%d"))
            else:
                process_date = None

            # matches_tc_vkn_no = re.findall(r'\d+', str(row['Açıklama']))
            # tc_vkn_no = matches_tc_vkn_no[-1] if matches_tc_vkn_no else None

            tc_vkn_no = str(row['Gönderen TCKN / VKN']) if not pd.isna(row['Gönderen TCKN / VKN']) else ""

            obj = BankActivity.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                bank_code = str(row['Banka Kodu']) if not pd.isna(row['Banka Kodu']) else "",
                bank_branch_code = str(row['Şube Kodu']) if not pd.isna(row['Şube Kodu']) else "",
                bank_account_no = str(row['Hesap Numarası']) if not pd.isna(row['Hesap Numarası']) else "",
                cross_bank_code = str(row['Karşı Banka']) if not pd.isna(row['Karşı Banka']) else "",
                cross_bank_branch_code = str(row['Karşı Şube']) if not pd.isna(row['Karşı Şube']) else "",
                cross_bank_account_no = str(row['Karşı Hesap']) if not pd.isna(row['Karşı Hesap']) else "",
                process_code = str(row['İşlem Kodu']) if not pd.isna(row['İşlem Kodu']) else "",
                credit_or_debit = str(row['Borç / Alacak']) if not pd.isna(row['Borç / Alacak']) else "",
                kontrat_no = str(row['Kontrat No']) if not pd.isna(row['Kontrat No']) else "",
                process_date_date = process_date,
                #process_type = "in" if str(row['İşlem Tipi']) == "+" else "out",
                amount = Decimal(str(row['Tutar']).replace(",",".")) if not pd.isna(row['Tutar']) else Decimal(str(0)),
                currency = Currency.objects.select_related().filter(code = "TRY" if row["Döviz Kodu"] == "YTL" else row["Döviz Cinsi"]).first() or None,
                name = str(row['Gönderen Ünvanı']) if not pd.isna(row['Gönderen Ünvanı']) else "",
                description = str(row['Açıklama']) if not pd.isna(row['Açıklama']) else "",
                tc_vkn_no = tc_vkn_no,
            )

            # if leases:
            #     obj.leases.add(*leases)

            #     processed_amount = obj.amount
            #     for lease in leases:
            #         installments = lease.lease_installments.all()
            #         total_overdue_amount = Decimal("0")
            #         for installment in installments:
            #             total_overdue_amount += installment.overdue_amount
            #         if total_overdue_amount > 0:
            #             lease.leaseflex_automation = True
            #             if processed_amount > 0:
            #                 if total_overdue_amount <= processed_amount:
            #                     lease.processed_amount = total_overdue_amount
            #                     processed_amount -= total_overdue_amount
            #                 else:
            #                     lease.processed_amount = processed_amount
            #                     processed_amount = 0
            #             else:
            #                 lease.leaseflex_automation = False
            #             lease.save()

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

def export_bank_activities(self):
    bank_activities = BankActivity.objects.select_related().filter().order_by("id")
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
                data["3. Şahıs Ödemesi"].append("Evet" if ba_lease.is_third_person else "")
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
            data["3. Şahıs Ödemesi"].append("")
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

    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__lease_installments__payment_date=today) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        )
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days')
    ).exclude(types__contains=["special"]).order_by('-max_overdue_days')

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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        #metin = f"Bilgilendirme: Sinpaş Kızılbük projesi’ne ait {today.strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatır, iyi günler dileriz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne ait {today.strftime('%d.%m.%Y')} tarihli taksit ödemenizi hatırlatır, online ödeme sistemimizden veya EFT/Havale yoluyla gerçekleştirmenizi rica ederiz. Ödeme yapıldıysa mesajı dikkate almayınız. İyi günler dileriz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
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

    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__lease_installments__payment_date=tomorrow) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        )
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days')
        ).exclude(types__contains=["special"]).order_by('-max_overdue_days')

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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne  ait {tomorrow.strftime('%d.%m.%Y')} tarihli taksit ödemeniz yaklaşmaktadır. Ödeme gününü hatırlatır, iyi günler dileriz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
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

def export_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__overdue_days__lte=30) &
        Q(partner_contracts__contract_leases__overdue_amount__gt=100) &
        Q(partner_contracts__contract_warning_notices__isnull=True) &
        #Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    )
    
    if str(self.params["project"]) == "diger":
        objs = objs.exclude(partner_contracts__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
    elif str(self.params["project"]) == "kizilbuk":
        objs = objs.filter(partner_contracts__vendor__crm_code__in=["11802","20559"])
    else:
        objs = objs.filter(partner_contracts__vendor__crm_code=str(self.params["project"]))

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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__lte=30) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        ).order_by("-overdue_amount")

        if str(self.params["project"]) == "diger":
            leases = leases.exclude(contract__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
        elif str(self.params["project"]) == "kizilbuk":
            leases = leases.filter(contract__vendor__crm_code__in=["11802","20559"])
        else:
            leases = leases.filter(contract__vendor__crm_code=str(self.params["project"]))
        
        total_overdue_amount = 0
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount
        
            metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne ait {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        else:
             metin = ""

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
        data["Tutar"].append(total_overdue_amount)
        data["Metin"].append(metin)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-risk-durumunda-olanlar.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_kdv_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__overdue_amount__gt=100) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=True)
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

def export_to_warned_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__overdue_amount__gt=1000) &
        Q(partner_contracts__contract_leases__overdue_days__gt=30) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False)
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True)
    ).exclude(
        Q(types__contains=["special"]) |
        Q(types__contains=["barter"]) |
        Q(types__contains=["virman"])
    ).filter(warning_notice_count=0)

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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            Q(overdue_amount__gt=1000) &
            Q(overdue_days__gt=30) &
            Q(contract__currency__code="TRY") &
            Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff = False)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(
             Q(contract__partner__types__contains=["special"]) |
             Q(contract__partner__types__contains=["barter"]) |
             Q(contract__partner__types__contains=["virman"])
        )

        total_overdue_amount = Decimal("0")
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount
        
            metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne ait {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        else:
             metin = ""

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
        data["Tutar"].append(total_overdue_amount)
        data["Metin"].append(metin)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "to_warned_risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilecekler.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_warned_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__overdue_amount__gt=1000) &
        Q(partner_contracts__contract_leases__overdue_days__gt=30) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False)
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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            Q(overdue_amount__gt=1000) &
            Q(overdue_days__gt=30) &
            Q(contract__currency__code="TRY") &
            Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff = False)
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
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount
        
            metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne ait {format_currency_tr(total_overdue_amount)} TL ödenmemiş taksitiniz bulunmaktadır. Takip sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        else:
             metin = ""

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
        data["Tutar"].append(total_overdue_amount)
        data["Metin"].append(metin)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "warned_risk_partners", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-ihtar-çekilenler.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()

def export_to_terminated_risk_partners(self):
    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__overdue_amount__gt=1000) &
        Q(partner_contracts__contract_leases__overdue_days__gt=30) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        ) &
        #Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=now().date()) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False) 
    ).annotate(
        max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
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
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            Q(overdue_amount__gt=1000) &
            Q(overdue_days__gt=30) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today()) &
            Q(contract__currency__code="TRY") &
            Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff = False)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count__gt=0).order_by("contract__code","-activation_date").exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )

        total_overdue_amount = Decimal("0")
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount
        
            metin = f"Değerli müşterimiz, Sinpaş Kızılbük projesi’ne {format_currency_tr(total_overdue_amount)} TL ihtar bakiyeniz bulunmaktadır. Fesih sürecindeki ödemenizi gerçekleştirmenizi rica ederiz. Arı Finansal Kiralama Tel:02123102721 Mernis No:0147005285500018"
        else:
             metin = ""

        data["Müşteri İsmi"].append(obj.name)
        data["TC/VKN No"].append(obj.tc_vkn_no)
        data["Crm Kodu"].append(obj.crm_code)
        data["Tel"].append(obj.phone_number if obj.phone_number else "")
        data["Email"].append(obj.email if obj.email else "")
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

def export_delivery_confirms(self):
    objs = Partner.objects.select_related().filter(
        Q(partner_contracts__contract_leases__overdue_amount=0) &
        Q(partner_contracts__contract_leases__is_kdv_diff=False) &
        Q(partner_contracts__contract_leases__paid_rate__gte=30) &
        Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
        (
            Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
            Q(partner_contracts__contract_leases__lease_status='planlandi') |
            Q(partner_contracts__contract_leases__lease_status='durduruldu')
        )
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
        "Sözleşme No": [],
        "Tahsilat Oranı": [],
        "Gecikmiş Bakiye": [],
        "Blok": [],
        "Bağımsız Bölüm": [],
        "Müşteri İsmi": [],
        "Müşteri TC": [],
        "Müşteri Tel": [],
        "Müşteri CRM Kodu": []
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress
        
        leases = Lease.objects.select_related().filter(
             Q(contract__partner = obj) &
             Q(contract__contract_leases__is_kdv_diff=False) &
             Q(contract__contract_leases__paid_rate__gte=30) &
             Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff = False)
        ).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        ).order_by("contract__code","-activation_date").distinct("contract__code")

        total_overdue_amount = Decimal("0")
        if leases:
            for lease in leases:
                total_overdue_amount += lease.overdue_amount

                data["Sözleşme No"].append(lease.contract.code)
                data["Tahsilat Oranı"].append(lease.paid_rate)
                data["Gecikmiş Bakiye"].append(lease.overdue_amount)
                data["Blok"].append(lease.contract.quotation_obj.quick_quotation.block if lease.contract.quotation_obj and lease.contract.quotation_obj.quick_quotation else "")
                data["Bağımsız Bölüm"].append(lease.contract.quotation_obj.quick_quotation.unit if lease.contract.quotation_obj and lease.contract.quotation_obj.quick_quotation else "")
                data["Müşteri İsmi"].append(lease.contract.partner.name)
                data["Müşteri TC"].append(lease.contract.partner.tc_vkn_no)
                data["Müşteri Tel"].append(lease.contract.partner.phone_number)
                data["Müşteri CRM Kodu"].append(lease.contract.partner.crm_code)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "leasing", "delivery_confirms", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-teslim-onay.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sayfa', index=False)
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()