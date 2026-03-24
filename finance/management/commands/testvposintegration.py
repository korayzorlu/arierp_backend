from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from finance.models import *
from finance.tasks import fetch_partner_advances

import pandas as pd
import json
import os
import pyodbc

from zeep import Client
from zeep.transports import Transport
import requests

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def handle(self, *args, **options):
        print("processing...")

        url = "http://localhost:8000/api/finance/add_vpos_transaction/"

        payload = {
            "CompanyId": "8ca8cc74-02d6-417e-bd4c-6568286187a3",
            "ValidationKey": "789ABC_xY2pQ9kL5mN8oR3sT6uV1wX4zE7fG",
            "UserName": "pflex",
            "Password": "pflex123",
            "ProcessDate": "2026-03-24T12:35:58Z",
            "MusteriTipi": 1,
            "PaidAmount": 150000.00,
            "CurrencyCode": "TL",
            "LeasePostingGroupId": True,
            "FirmaAdi": "Örnek Firma A.Ş.",
            "KurumTipi": "LimitedSirketi",
            "VergiDairesi": "Kadıköy",
            "VergiNo": "1234567890",
            "WebSitesi": "https://ornekfirma.com",
            "Adres": "Atatürk Cad. No:1",
            "Ulke": "Türkiye",
            "Sehir": "İstanbul",
            "Ilce": "Kadıköy",
            "Posta": "34710",
            "IletisimList": [
                { "IletisimTuru": "Telefon", "IletisimDegeri": "+905001234567" },
                { "IletisimTuru": "Email", "IletisimDegeri": "info@ornekfirma.com" }
            ],

            "Ad": "Ahmet",
            "IkinciAd": "",
            "OrtaAd": "",
            "SoyAd": "Yılmaz",
            "Cinsiyet": "E",
            "TCKimlikNo": "12345678901",
            "PasaportNo": "",
            "Uyruk": "TC",
            "DogumTarih": "1990-05-15",
            "VergiDairesi_Birey": "Kadıköy",
            "VergiNo_Birey": "1234567890",
            "Adres_Birey": "Atatürk Cad. No:1",
            "Ulke_Birey": "Türkiye",
            "Sehir_Birey": "İstanbul",
            "Ilce_Birey": "Kadıköy",
            "Posta_Birey": "34710",
            "IletisimList_Birey": [
                { "IletisimTuru": "Telefon", "IletisimDegeri": "+905001234567" },
                { "IletisimTuru": "Email", "IletisimDegeri": "ahmet@email.com" }
            ],

            "UserName": "kullanici_adi",
            "Password": "sifre",
            "Telefon": "+905001234567",
            "EMail": "info@ornekfirma.com",
            "Fax": "",
            "BankCode": "0001",
            "ContractCode": "KONTR-001",
            "CurrencyCode": "TRY",
            "ExtTransactionId": "EXT-TX-001"
        }

        response = requests.post(url, json=payload)
        print(response.status_code, response.json())

        print("done!")