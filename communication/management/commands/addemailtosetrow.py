from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import pandas as pd
import json
import os
import pyodbc
import requests

from common.utils.common_utils import LegacyTLSAdapter

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')
        parser.add_argument('-e', type=str, help='Email to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')
        email = options.get('e')

        print("processing...")
        
        url = f"https://api.setrow.com/V1/setrow_emailadres_tanimlama.php?k={settings.SETROW_API_KEY}&adres={email}"

        headers = {
            "Authorization": f"Bearer {settings.SETROW_API_KEY}",
        }
        payload = {
            "k" : settings.SETROW_API_KEY,
            "adres" : email,
        }
        session = requests.Session()
        session.mount("https://", LegacyTLSAdapter())

        response = session.get(url, headers=headers)
        print(response.status_code, response.text)
        
        print("done!")