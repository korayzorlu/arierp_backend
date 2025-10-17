from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from communication.utils.turatel_utils import *
from contracts.models import *
from leasing.models import *
from accounting.tasks import fetch_trial_balances

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
        
        phone_numbers = ["05542663970","05542663970"]
        messageParameters = [
            {
                "parameter": [
                    "Koray Zorlu",
                    "100 TL"
                ]
            },
            {
                "parameter": [
                    "Koray Zorluu",
                    "100 TL"
                ]
            },
        ]

        if len(phone_numbers) != len(messageParameters):
            return "Telefon listesi ile mesaj listesi uyuşmuyor."

        params = {
            "messageText" : "Sayın[##parameter1##], Test mesajıdır. Lütfen dikkate almayınız. Tutar: [##parameter2##]. İyi günler dileriz.",
            "receiverList" : phone_numbers,
            "personalMessages" : messageParameters
        }

        response = get_turatel_send_sms(params)
        print(response)
        
        print("done!")