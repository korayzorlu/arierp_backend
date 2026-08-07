from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from emlak.utils import make_whatsapp_message
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

        data = {
            "company" : company,
            "name" : "Seda Güneş",
            "phone_number_1" : "0 (216) 807 11 22",
            "phone_number_2" : "0 (539) 821 10 29",
            "ilan_no" : "1329471024",
            "amount" : "5.550.000",
            "meet_date" : "2026-08-12",
        }
        
        make_whatsapp_message(data)
        
        print("done!")