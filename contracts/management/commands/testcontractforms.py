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

        url = "https://arinet.arileasing.com.tr/api/contracts/create_contract_forms/"

        payload = {
            "CompanyId": "8ca8cc74-02d6-417e-bd4c-6568286187a3",
            "ValidationKey": "YXmyHBzEbUvIOv42te8WkyijEzgHQFS1kLiSPk9dx9o",
            "ContractHeaderCode": "95712",
            "CustomerName": "Ahmet Yılmaz",
            "TaxAndTCIdentity": "12345678901",
            "YazismaAddress": "Atatürk Cad. No:1 Kadıköy/İSTANBUL",
            "WorkPhone": "2161234567",
            "OtherAddress": "Test Other Address",
            "MobilPhone": "5445555566",
            "OtherPhone": "0987654321",
            "Email": "test@example.com",
            "Kep": "test@example.com",
            "IslandNo": "12",
            "ParcelNo": "56",
            "ProjectName": "SiNPAŞ KASABA THERMAL WELLNESS RESORT",
            "FreePartUnitType": "3+1",
            "ApartmentTypeName": "TOWN GRAND HOME",
            "FreeValidationPeriodText": "LONG",
            "TimeSharePeriodPartText": "3.dönem ('15 Ocak - 21 Ocak taribleri arasi)",
            "NumberOfPeopleStay": 2,
            "CustomerSignDate": "2026-06-01",
            "TaxRate": 20,
            "PlannedDeliveryDate": "2026-07-01",
            "Maturity": 36,
            "CashSalesTotalAmount": "1195116.00 ",
            "LeasingAmount": "101712.00",
            "CurrentSaleTotalAmount": "1296828.00",
            "DownPaymentAmount": "5000.00",
            "CurrencyCode": "TRY"
        }

        response = requests.post(
            url,
            json=payload,
            cert=(
                "/mnt/c/Users/koray.zorlu/projects/arierp/arierp_backend/certs/client-cert.pem",
                "/mnt/c/Users/koray.zorlu/projects/arierp/arierp_backend/certs/client-key.pem"
            ),
            verify=False
        )
        print(response.status_code, response.json())

        print("done!")