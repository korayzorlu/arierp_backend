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

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")
        
        url = f"https://www.setrowsend.com/email/sendV2.php?k={settings.SETROW_API_KEY}&ktemplate=b84e83786dbcbc132b0b25d293890ba6506ff7d0b474b2aa4e"

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

        response = session.post(url, headers=headers, json=payload)
        print(response.status_code, response.text)
        
        print("done!")