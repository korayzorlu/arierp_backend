from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from finance.models import *
from finance.tasks import fetch_finmaks_transactions

import pandas as pd
import json
import os
import pyodbc
import requests

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")

        excel_file = pd.ExcelFile("files/guncel-tapu.xlsx")
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel("files/guncel-tapu.xlsx", sheet_name)
        df = pd.DataFrame(file_data)

        search_word = "depo"
        folder_path = "files/depo"
            

        print("done!")