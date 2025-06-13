from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import BooleanField

import pandas as pd
import io
import os
from decimal import Decimal
from openai import OpenAI
import time
import ast

from users.models import User
from common.models import ImportProcess
from partners.models import Partner
from converters.models import BankaHareketi, BankaTahsilati, BankaTahsilatiOdoo

from dotenv import load_dotenv
load_dotenv()

class BaseImporter():
    allowed_extensions = ["xls", "xlsx"]
    max_file_size = 10 * 1024 * 1024
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

