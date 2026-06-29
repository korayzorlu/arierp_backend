from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models.functions import Replace

from communication.utils.turatel_utils import *
from contracts.models import *
from leasing.models import *
from accounting.tasks import fetch_trial_balances
from partners.models import Partner

import pandas as pd
import json
import os
import pyodbc
import requests

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
        
        url = "https://integration-voyce.voyce.arileasing.com.tr/integration-voyce/v1/CdrDetails"

        headers = {
            "Authorization": "sk-v1-jVGfakpqhzF7VGpcgW6N9",
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        payload = {
            "RemoteNumber": "05322346968",
            "StartTime": "2026-05-24T08:00:00Z",
            "EndTime": "2026-06-25T18:00:00Z",
        }

#         curl --request POST \
#   --url https://api.live.voyce.arileasing.com.tr/integration-voyce/v1/CdrDetails \
#   --cacert /mnt/c/Users/koray.zorlu/projects/arierp/arierp_backend/VOYCE_CA.crt \
#   --header 'Accept: application/json' \
#   --header 'Authorization: sk-v1bVYQdkBzz4KntX4i9NUGLd' \
#   --header 'Content-Type: application/json' \
#   --data '{
#   "StartTime": "2025-09-10T09:00:00Z",
#   "EndTime": "2025-09-10T12:00:00Z",
#   "Verdict": "CONNECTED,NO_ANSWER"
# }'

        ca_path = os.path.join(settings.BASE_DIR, "VOYCE_CA.crt")

        response = requests.post(url, headers=headers, json=payload, verify=ca_path)
        
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            print(data)

            # print(data.get("Queue"))
            # print(data.get("RemoteNumber"))
            # print(data.get("StartTime"))
            # print(data.get("EndTime"))

            # partner = Partner.objects.filter().annotate(
            #     fixed_phone_number=Replace(
            #         Replace(
            #             Replace(
            #                 Replace(F("phone_number"), Value(" "), Value("")),
            #                 Value("-"), Value("")
            #             ),
            #             Value("("), Value("")
            #         ),
            #         Value(")"), Value("")
            #     )
            # ).filter(fixed_phone_number=data.get("RemoteNumber")).first()

            # print(partner)
        
        print("done!")