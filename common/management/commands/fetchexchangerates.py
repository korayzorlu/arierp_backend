from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.tasks import fetch_exchange_rates
from contracts.models import *
from leasing.models import *
from contracts.tasks import fetch_contract_payments

import pandas as pd
import json
import os
import pyodbc
import time

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Currency to associate with operation')
        parser.add_argument('-d', type=str, help='Date to fetch exchange rate for')

    def handle(self, *args, **options):
        target_currency = options.get('c')
        date = options.get('d')

        print("processing...")

        fetch_exchange_rates.delay(target_currency)

        print("done!")