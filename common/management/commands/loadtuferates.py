from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.timezone import now

from common.tasks import fetch_exchange_rates
from common.models import TufeRate
from contracts.models import *
from leasing.models import *
from contracts.tasks import fetch_contract_payments

import pandas as pd
import json
import os
import pyodbc
import time
from datetime import datetime,date,timedelta
import calendar

def previous_month_last_day(d: date) -> date:
    first_of_month = d.replace(day=1)
    return first_of_month - timedelta(days=1)

def days_in_month(d: date) -> int:
    return calendar.monthrange(d.year, d.month)[1]

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def handle(self, *args, **options):

        print("processing...")

        excel_file = pd.ExcelFile("files/tufe.xlsx")
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel("files/tufe.xlsx", sheet_name)
        df = pd.DataFrame(file_data)

        for index,row in df.iterrows():
            if not TufeRate.objects.filter(code=row['Dönem']).exists():
                month, year = map(int, row['Dönem'].split('-'))
                last_day_prev = calendar.monthrange(year, month)[1]
                date_value = datetime(year, month, last_day_prev).date()

                TufeRate.objects.create(
                    code = row['Dönem'],
                    date = date_value,
                    rate = Decimal(str(row['Değer'])),
                    change_rate = Decimal(str(row['Aylık Değişim'])),
                )

        

        print("done!")


        