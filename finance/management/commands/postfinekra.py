from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from finance.models import *
from finance.utils import fetch_finekra_token,fetch_finekra_banks,fetch_finekra_currencies,fetch_finekra_bank_accounts

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

        #get banks
        banks = fetch_finekra_banks()
            
        for bank in banks:
            print(bank)

        #get currencies
        currencies = fetch_finekra_currencies()

        for currency in currencies:
            print(currency)

        #get bank accounts
        bank_accounts = fetch_finekra_bank_accounts()

        for account in bank_accounts:
            print(account)

        print("done!")