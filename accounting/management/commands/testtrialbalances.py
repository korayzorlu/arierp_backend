from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from accounting.models import TrialBalance
from contracts.models import *
from leasing.models import *
from accounting.tasks import fetch_trial_balances

import pandas as pd
import json
import os
import pyodbc

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
        
        # Farklı main_account_code değerlerinin sayısını ve kendilerini yazdır
        main_account_codes = TrialBalance.objects.values_list('main_account_code', flat=True).distinct()
        print(f"Farklı main_account_code sayısı: {main_account_codes.count()}")
        print("main_account_code değerleri:")
        for code in main_account_codes:
            print(code)



        # code = "393"

        # first_code = code.split('.')[0] if code else ''
        # print(first_code)
        
        print("done!")