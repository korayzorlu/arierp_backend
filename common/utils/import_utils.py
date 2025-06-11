from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import BooleanField

import pandas as pd
import io
import os
from decimal import Decimal

from users.models import User
from common.models import ImportProcess
from partners.models import Partner
from converters.models import BankaHareketi, BankaTahsilati, BankaTahsilatiOdoo

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

    def import_hareketi(self, df_json):
        df = pd.read_json(io.StringIO(df_json), orient='records')
        
        required_columns = ["Açıklama"]
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
            
            obj = BankaHareketi.objects.create(
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

