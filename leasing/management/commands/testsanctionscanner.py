from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *
from leasing.tasks import fetch_leases

import pandas as pd
import json
import os
import pyodbc
import requests
from requests.auth import HTTPBasicAuth

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def handle(self, *args, **options):
        print("processing...")
        
        

        # API kullanıcı bilgileri
        USERNAME = "960ed49f-7588-467e-9c3c-58a4f32acc2b"
        PASSWORD = "hZu8zUJfwF"

        # Aranacak isim ve isteğe bağlı parametreler
        params = {
            "name": "Özgür Özel",     # en az 3 karakter
            "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
            "start": 0,                 # sayfalama başlangıcı
            "limit": 20,                # maksimum 50
            #"birthYear": "1980",
            "minMatchRate": 95,
            "isDeepSearch": True
        }

        response = requests.get(
            "https://sandbox-api.sanctionscanner.com/api/Search/SearchByName",
            params=params,
            auth=HTTPBasicAuth(USERNAME, PASSWORD)
        ).json()

        for item in response["Result"]["Result"]:
            print(f"FullName: {item["FullName"]} |MatchRate: {item["MatchRate"]} | Type: {item["Type"]} | ")


        print(f"Temiz mi?: {"Temiz" if len(response["Result"]["Result"]) == 0 else "Sorunlu"} | Pep mi?: ")
        
        print("done!")