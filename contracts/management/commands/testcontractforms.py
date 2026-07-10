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

        url = "http://localhost:8000/api/contracts/create_contract_forms/"

        payload = {
            "CompanyId": "8ca8cc74-02d6-417e-bd4c-6568286187a3",
            "ValidationKey": "YXmyHBzEbUvIOv42te8WkyijEzgHQFS1kLiSPk9dx9o",
            "ContractHeaderCode": "75212",
            "CustomerName": "Koray Zorlu",
            "TaxAndTCIdentity": "12345678901",
            "YazismaAddress": "Test Address",
            "WorkPhone": "1234567890",
            "OtherAddress": "Test Other Address",
            "MobilPhone": "5555555555",
            "OtherPhone": "0987654321",
            "Email": "test@example.com",
            "KepAddress": "test@example.com"
        }

        response = requests.post(url, json=payload)
        print(response.status_code, response.json())

        print("done!")