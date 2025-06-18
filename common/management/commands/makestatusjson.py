from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

        excel_file = pd.ExcelFile("files/statuler.xlsx")
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel("files/statuler.xlsx", sheet_name)
        df = pd.DataFrame(file_data)
        
        new_list = []

        for index,row in df.iterrows():
            new_list.append({
                "model" : "common.status",
                "pk" : index + 1,
                "fields" : {
                    "model" : row["model"],
                    "main_status" : int(row["main_status"]) if row["main_status"] else None,
                    "name" : row["Tanım"]
                }
            })

        with open(os.path.join(settings.BASE_DIR, "common/fixtures/status-model.json"), "w") as f:
            json.dump(new_list, f)
        
        print("done!")