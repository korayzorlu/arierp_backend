from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *
from communication.tasks import fetch_calls_task

import pandas as pd
import json
import os
import pyodbc

class Command(BaseCommand):
    help = 'Fetches calls from Voyce'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')
        parser.add_argument('-s', type=str, help='Start date for fetching calls')
        parser.add_argument('-e', type=str, help='End date for fetching calls')

    def handle(self, *args, **options):
        company = options.get('c')
        start_date = options.get('s')
        end_date = options.get('e')

        print("processing...")
        
        fetch_calls_task.delay({"company": company, "start_date": start_date, "end_date": end_date})
        
        print("done!")