from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from trade.tasks import fetch_trade_transactions
from contracts.models import *
from leasing.models import *
from partners.tasks import fetch_partners

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
        parser.add_argument('-k', type=str, help='Contract ID to associate with operation')
        parser.add_argument('-a', action='store_true', default=False, help='All flag for operation')

    def handle(self, *args, **options):
        company = options.get('c')
        contract_code = options.get('k')
        all = options.get('a')

        print("processing...")

        fetch_trade_transactions.delay(company, contract_code=contract_code, all=all)
        print("done!")