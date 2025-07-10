from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import BooleanField,QuerySet, Q
from django.db.models.functions import Lower,Upper

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
from leasing.utils import export_bank_activities

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

class BaseExporter():
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

    def start_export(self, df_json):
        from common.tasks import exportData
        exportData.delay(df_json, self.user.id, self.app, self.model_name)

    def process_export(self, df_json):
        self.process = ImportProcess.objects.create(
            company = self.user.user_companies.filter(is_active=True).first().company,
            user = self.user,
            model_name = self.model_name,
            task_id = self.task_id
        )
        self.process.save()
        
        export_function = getattr(self, f"export_{self.model_name.lower()}", None)
        if not export_function:
            self.process.status = "rejected"
            self.process.save()
            return {"message": "Sorry, something went wrong! [CM0001]"}

        export_function(df_json)

        self.process.progress = 100
        self.process.status = "completed"
        self.process.save()
    
    def export_bankactivity(self, df_json):
        export_bank_activities(self, df_json)

 