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
        
        current_bank_activities = BankActivity.objects.select_related().filter(created_date__date = date.today())
        if current_bank_activities:
            current_bank_activities.delete()

        current_leases = Lease.objects.select_related().filter(leaseflex_automation = True)
        for current_lease in current_leases:
            current_lease.leaseflex_automation = False
            current_lease.processed_amount = Decimal("0")
            current_lease.save()
        
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

            tc_vkn_no = str(int(row['Gönderen TCKN / VKN'])) if not pd.isna(row['Gönderen TCKN / VKN']) else ""
            
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
                tc_vkn_no = tc_vkn_no
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

