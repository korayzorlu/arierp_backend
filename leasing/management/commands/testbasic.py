from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os
from bs4 import BeautifulSoup
import pyodbc
from decimal import Decimal
from datetime import datetime

from leasing.models import Lease,Installment

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

        formatted_today = datetime.now().date()
        formatted_today = f"{formatted_today.year}-{formatted_today.month}-{formatted_today.day}"

        print(formatted_today)
        
        
        print("done!")