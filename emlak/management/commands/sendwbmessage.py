from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from emlak.utils import make_whatsapp_message,send_test_wb_message
from companies.models import Company

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

        company = Company.objects.filter(id=int(company)).first()

        send_test_wb_message()
        
        print("done!")