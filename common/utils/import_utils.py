from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import BooleanField,QuerySet, Q
from django.db.models.functions import Lower,Upper
from django.utils.crypto import get_random_string
from django.utils.timezone import localtime, make_aware, is_naive


import pandas as pd
import io
import os
from decimal import Decimal
from openai import OpenAI
from datetime import datetime
import time
import ast
import pickle

from users.models import User
from common.models import ImportProcess,Country,City
from partners.models import Partner,Sector
from converters.models import BankaHareketi, BankaTahsilati, BankaTahsilatiOdoo
from leasing.models import Lease,BankActivity
from compliance.models import ThirdPerson
from compliance.utils.third_person_utils import create_third_person
from finance.models import FinmaksTransaction,FinmaksBankAccount
from underwriting.utils import check_third_person_status
from contracts.utils.contract_utils import import_contracts
from leasing.utils.import_utils import import_leases,import_installments,import_bank_activities
from risk.utils.import_utils import import_overdue_leases
from quotations.utils.quotation_utils import import_quotations
from quotations.utils.quick_quotation_utils import import_quick_quotations

from dotenv import load_dotenv
load_dotenv()

def save_pickle_to_file(data, prefix="import_data"):
    os.makedirs("/media/tmp/imports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{prefix}_{timestamp}.pkl"
    filepath = os.path.join("/media/tmp/imports", filename)

    with open(filepath, "wb") as f:
        pickle.dump(data, f)

    return filepath

class BaseImporter():
    allowed_extensions = ["xls", "xlsx"]
    max_file_size = 100 * 1024 * 1024
    max_rows = 10_000

    expected_columns = {
        "partner": []
    }

    def __init__(self, user_id, app, model_name, file=None, task_id=None):
        self.file = file
        self.user = User.objects.filter(id = int(user_id)).first()
        self.app = app
        self.model_name = model_name
        self.model = self.get_model()
        self.task_id = task_id
        self.process = None
        self.df = None

    def get_model(self):
        try:
            return apps.get_model(self.app, self.model_name)
        except LookupError:
            return None

    def validate_file(self):
        if not self.file:
            return {"message": "File not found!"}
        
        file_size = self.file.size
        if file_size > self.max_file_size:
            return {"message": f"File too large! Max {self.max_file_size // (1024 * 1024)}MB allowed."}

        file_name, file_extension = os.path.splitext(self.file.name)
        file_extension = file_extension.lower().lstrip('.')

        if file_extension not in self.allowed_extensions:   
            return {"message": "Invalid file type! Only Excel files are allowed."}

        return 200
    
    def get_required_fields(self):
        excluded_fields = {}

        return [
            field.name for field in self.model._meta.fields
            if not field.null and not field.blank and not isinstance(field, BooleanField) and field.name not in excluded_fields
        ]

    def read_file(self):
        try:
            excel_file = pd.ExcelFile(self.file)
            first_sheet_name = excel_file.sheet_names[0]
            
            file_data = pd.read_excel(self.file, first_sheet_name)
            df = pd.DataFrame(file_data)
            self.df = df

            # required_fields = set(self.get_required_fields())
            # df_columns = set(df.columns)
            # missing_columns = required_fields - df_columns

            # if missing_columns:
            #     return {"message":f"Missing required columns: {list(missing_columns)}"}

            return df.to_json(orient='records')
        except Exception as e:
            return {"message": f"File read error: {str(e)}"}

    def start_import(self, df_json):
        from common.tasks import importData
        importData.delay(df_json, self.user.id, self.app, self.model_name)

    def process_import(self, df_json):
        self.process = ImportProcess.objects.create(
            company = self.user.user_companies.filter(is_active=True).first().company,
            user = self.user,
            model_name = self.model_name,
            task_id = self.task_id
        )
        self.process.save()

        import_function = getattr(self, f"import_{self.model_name.lower()}", None)
        if not import_function:
            self.process.status = "rejected"
            self.process.save()
            return {"message": "Sorry, something went wrong! [CM0001]"}
        
        import_function(df_json)

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

    def import_sector(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = ["Sektör No","Sektör Adı"]
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

            #process commands

            obj = Sector.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                code = row["Sektör No"],
                name = row["Sektör Adı"],
                main_sector_code = row["Ana Sektör No"],
                match_code = row["Eşleştirme Kodu"],
                kkbmb_sector_code = row["KKBMBSectorCode"],
            )
            obj.save()
            #process commands end

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

    def import_partner(self, df_json):
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

            obj = Partner.objects.filter(customer_code = str(row["Müşteri Kodu"])).first()
            if obj:
                obj.customer_code = str(int(row["Müşteri Kodu"]))
                obj.save()

            nanObjs = Partner.objects.filter(customer_code = "nan")
            for nanObj in nanObjs:
                nanObj.customer_code = None
                nanObj.save()

            """
            if Partner.objects.filter(tc_vkn_no = row["Vergi/TC Kimlik No"], name = row["Ad Soyad"], birthday=datetime.strptime(row["Doğum Tarihi"], "%d.%m.%Y").date() if row["Doğum Tarihi"] else None).exists():
                continue

            if row["İkinci Adı"]:
                if len(row["İkinci Adı"]) > 0:
                    first_name = f"{row['Adı']} {row['İkinci Adı']}"
            else:
                first_name = row["Adı"]

            if row["Ülke Kodu"] == "İNG":
                row["Ülke Kodu"] = "UK"

            if row["Doğum Tarihi"]:
                birthday = datetime.strptime(row["Doğum Tarihi"], "%d.%m.%Y").date()
            else:
                birthday = None

            if row["Kep Bitiş Tarihi"]:
                kep_expiry_date = datetime.strptime(row["Kep Bitiş Tarihi"], "%d.%m.%Y").date()
            else:
                kep_expiry_date = None
            
            partner = Partner.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                first_name = first_name,
                last_name = row["Soyad"],
                name = row["Ad Soyad"],
                formal_name = row["Kurum"],
                customer_code = str(int(row["Müşteri Kodu"])),
                vat_no = str(row.get("Vergi No")) or None,
                vat_office = row.get("Vergi Dairesi") or None,
                tc_no = row["TC Kimlik No"],
                tc_vkn_no = row["Vergi/TC Kimlik No"],
                passport_no = row["Pasaport No"],
                ticari_sicil_no = row["Ticari Sicil No"],
                kep = row["Kep Adresi"],
                kep_expiry_date = kep_expiry_date,
                is_turkkep = True if row["Türkkep Müşterisi Mi ?"] == "Evet" else False,
                sector = Sector.objects.filter(code = str(row["Ana Faaliyet Sektör Adı"])).first(),
                father_name = row["Baba Adı"],
                birthday = birthday,
                country = Country.objects.filter(iso2 = row["Ülke Kodu"]).first(),
                city = City.objects.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = row["Şehir Adı"] or "xxx") | Q(uppercase__icontains = row["Şehir Adı"] or "xxx")).first(),
                address = row["Adres"][:250] if row["Adres"] else None,
                phone_number = row.get("Telefon") or None,
                email = row.get("Email") or None,
                types = ["customer"]
            )
            partner.save()
            """
        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

    


    def import_contract(self, df_json):
        import_contracts(self, df_json)

    def import_lease(self, df_json):
        import_leases(self, df_json)

    def import_installment(self, df_json):
        import_installments(self, df_json)

    def import_bankactivity(self, df_json):
        import_bank_activities(self, df_json)

    def import_quickquotation(self, df_json):
        import_quick_quotations(self, df_json)

    def import_quotation(self, df_json):
        import_quotations(self, df_json)

    def import_bankahareketi(self, df_json):
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
        
        new_list = []
        for index,row in df.iterrows():
            self.process.progress = 20
            self.process.save()

            #process commands
            # if row.get("SÖZLEŞME DIŞI-3.ŞAHIS"):
            #     if row["SÖZLEŞME DIŞI-3.ŞAHIS"] == "EVET":
            #         ucuncu_sahis_mi = True
            #     else:
            #         ucuncu_sahis_mi = False
            # else:
            #     ucuncu_sahis_mi = False

            new_list.append({
                "aciklama" : row.get("Açıklama") or None,
                "ucuncu_sahis_mi" : False
            })

            

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.responses.create(
            model="gpt-4.1",
            #input=f"{row.get("Açıklama")} bu havale/eft açıklamasında 'gelen eft', 'gelen havale' veya 'gelen fast' yazısından sonraki isim parayı gönderen kişiye ait. gönderen kişinin ismi iki defa yazıyor, iki isim arasındaki yazı para transferinin açıklama yazısı. bu açıklama kısmını incele ve ödemenin parayı göndren tarafından başkası adına yapıp yapmadığını noktalama olmadan evet veya hayır diyerek cevapla, başka hiçbir şey yazma."
            input=f"{new_list} bu listedeki açıklama kısımlarında havale/eft açıklamasında 'gelen eft', 'gelen havale' veya 'gelen fast' yazılarındandan sonraki isim parayı gönderen kişiye ait. gönderen kişinin ismi iki defa yazıyor, iki isim arasındaki yazı para transferinin açıklama yazısı. bu açıklama kısmımlarını incele ve ödemenin parayı göndren tarafından başkası adına yapıp yapmadığını analiz et. eğer başkasına yapmışsa 'ucuncu_sahis_mi' kısmını True yap değil False kalsın. En son güncel listeyti yaz sadece başka hiçbir şey yazma."
        )

        response_list = ast.literal_eval(response.output_text)

        self.process.progress = 60
        self.process.save()

        previous_progress = 0
        for item in response_list:
            current_progress = ((index + 1)/len(df))*100

            if current_progress - previous_progress >= 5:
                self.process.progress = int(current_progress) + 60
                self.process.save()
                previous_progress = current_progress

            obj = BankaHareketi.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                gonderen_unvani = "test",
                musteri_unvani = "test",
                aciklama = item["aciklama"],
                ucuncu_sahis_mi = item["ucuncu_sahis_mi"],
                ucuncu_sahis_mi_str = "Evet" if item["ucuncu_sahis_mi"] else ""
            )
            obj.save()




            #process commands end



        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()
    
    def import_bankatahsilati(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = ["Gönderen TCKN / VKN"]
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

            #process commands

            if row["Hesap Numarası"] == 14651335 and row["Tutar"] >= 0:
                obj = BankaTahsilati.objects.create(
                    company = self.user.user_companies.filter(is_active=True).first().company,
                    gonderen_unvani = row["Gönderen Ünvanı"],
                    tc_vkn_no = row["Gönderen TCKN / VKN"],
                    tutar = Decimal(str(row["Tutar"])),
                    aciklama = row.get("Açıklama") or None,
                )
                obj.save()




            #process commands end

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

    def import_bankatahsilatiodoo(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = ["Gönderen TCKN / VKN"]
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

            #process commands


            obj = BankaTahsilatiOdoo.objects.create(
                company = self.user.user_companies.filter(is_active=True).first().company,
                gonderen_unvani = row["Gönderen Ünvanı"],
                tc_vkn_no = row["Gönderen TCKN / VKN"],
                tutar = Decimal(str(row["Tutar"])),
                aciklama = row.get("Açıklama") or None,
            )
            obj.save()




            #process commands end

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

    def import_thirdperson(self, df_json):
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

            bank_account = FinmaksBankAccount.objects.filter(account_no = "sanalpos-1").first()

            leases = Lease.objects.select_related("contract__partner").filter(code = str(row["Müşteri Telefon Numarası"]).replace("KiraPlanKodu: ","").split(",")[0])

            for lease in leases:
                if lease.contract.partner.name != row['Adı-Soyadı'].replace(' . ',' ').replace('  ',' '):
                    print(f"kira planı: {lease.code} - müşteri adı: {lease.contract.partner.name} - ödemeyi yapan: {row['Adı-Soyadı'].replace(' . ',' ').replace('  ',' ')}")

                    # ThirdPerson.objects.create(
                    #     company = self.user.user_companies.filter(is_active=True).first().company,
                    #     name = row['Adı-Soyadı'].replace(' . ',' ').replace('  ',' '),
                    #     tc_vkn_passport_no = str(row['Vergi/TC Kimlik No']),
                    #     lease = lease,
                    #     is_vpos = True
                    # )

                    # scan_result = check_third_person_status(row['Adı-Soyadı'].replace(' . ',' ').replace('  ',' '))
                    # third_person = create_third_person(self,scan_result)

                    

                    finmaks_transaction = FinmaksTransaction.objects.create(
                        company = lease.company,
                        bank_account = bank_account,
                        transaction_id = f"T{get_random_string(length=6, allowed_chars='0123456789')}",
                        transaction_date = datetime.now(),
                        explanation_field = f"Sanal pos ödemesi - İşlem No: {Decimal(row.get('Sipariş Numarası',''))}",
                        description = "",
                        amount = Decimal(str(row.get('İşlem Tutarı', '0.00'))),
                        sender_vkn = "",
                        sender_iban = "",
                        sender_account_name = row.get('Adı-Soyadı', '').replace(' . ',' ').replace('  ',' '),
                        receiver_vkn = "",
                        receiver_iban = "",
                        receipt_number = "",
                        value_date = datetime.now(),
                        transaction_type = "",
                        bank_code = "",
                        balance = Decimal('0.00'),
                        firm_id = "",
                        firm_name = "",
                        firm_externalCode = "",
                        firm_externalId = "",
                        transaction_branch_code = "",
                        transaction_branch_name = "",
                        firm_code = "",
                        currency_type = "TRY",
                        debit = "+",
                        branch_code = "",
                        transaction_external_id = "",
                        external_id_used = False,
                        external_bank_id = "",
                        reference_no = "",
                        finmaks_process_type = "",
                        category_name = "",
                        integration_field_value = "",
                        transaction_status = "",
                        is_vpos = True
                    )

                    if is_naive(finmaks_transaction.transaction_date):
                        aware_date = make_aware(finmaks_transaction.transaction_date)
                    else:
                        aware_date = finmaks_transaction.transaction_date

                    process_date_date = localtime(aware_date).date()

                    BankActivity.objects.create(
                        company = lease.company,
                        finmaks_transaction = finmaks_transaction,
                        bank_code = finmaks_transaction.bank_code,
                        bank_branch_code = finmaks_transaction.branch_code,
                        bank_account_no = finmaks_transaction.bank_account.account_no,
                        cross_bank_code = finmaks_transaction.bank_code,
                        cross_bank_branch_code = finmaks_transaction.transaction_branch_code,
                        cross_bank_account_no = finmaks_transaction.sender_iban,
                        process_code = finmaks_transaction.transaction_id,
                        credit_or_debit = "C" if finmaks_transaction.debit == "+" else "D",
                        kontrat_no = finmaks_transaction.receipt_number,
                        process_date_date = process_date_date,
                        #process_type = "in" if str(row['İşlem Tipi']) == "+" else "out",
                        amount = finmaks_transaction.amount,
                        currency = finmaks_transaction.bank_account.currency,
                        name = finmaks_transaction.sender_account_name,
                        description = finmaks_transaction.explanation_field,
                        tc_vkn_no = str(row['Kredi Kartı Numarası']),
                        is_vpos = True
                    )

                time.sleep(2)

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()

    def import_overduelease(self, df_json):
        import_overdue_leases(self, df_json)