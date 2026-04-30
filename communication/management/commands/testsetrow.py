from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import pandas as pd
import json
import os
import pyodbc
import requests
import xmltodict

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

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")
        
        url = (
            f"https://api.setrow.com/V1/TRANS_SONUC_V2.php"
            f"?apikey={settings.SETROW_API_KEY}"
            f"&date=2026-04-29"
            f"&type=2"
            f"&templatename=vadesi_gecmisler"
        )

        headers = {
            "Authorization": f"Bearer {settings.SETROW_API_KEY}",
        }
        payload = [
            {
                "to": "korayzorllu@gmail.com",
                "variables": {
                    "konu": "Ödeme Hatırlatma Bilgilendirmesi",
                    "proje": "SİNPAŞ KIZILBÜK",
                    "tutar": "156.897,00",
                },
            },
        ]

        session = requests.Session()
        session.mount("https://", LegacyTLSAdapter())

        response = session.get(url, headers=headers)

        data_dict = xmltodict.parse(response.content)
        data_json = json.dumps(data_dict, ensure_ascii=False, indent=2)

        print(data_json)
        
        print("done!")