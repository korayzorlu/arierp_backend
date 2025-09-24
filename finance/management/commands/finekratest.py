from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from finance.models import *

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

        ####
        #BASE_URL = "http://finekra.sinpas.com.tr"  # Gerekirse güncelleyin
        TOKEN = "eyJhbGciOiJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNobWFjLXNoYTI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJiOGZhMmRkMi1jYTkyLWYwMTEtYmY1Yy0wMDBjMjkxNGU5OTkiLCJ1c2VyZW1haWwiOiJ0ZXN0YXBpQHNpbnBhcy5jb20iLCJ1c2VybmFtZSI6IlRlc3QgQXBpIiwidGVuYW50aWQiOiJkMjI0ZDQyMi1iZDNmLWYwMTEtYmY1Yi0wMDBjMjkxNGU5OTkiLCJ0ZW5hbnR1c2VyaWQiOiJiOWZhMmRkMi1jYTkyLWYwMTEtYmY1Yy0wMDBjMjkxNGU5OTkiLCJ0ZW5hbnRuYW1lIjoiVGVrbmlrIFRlc3QgRmlybWFzxLEiLCJuYmYiOjE3NTgwMDYxMzIsImV4cCI6MTc1ODM1MTczMiwiaXNzIjoiZmluZWtyYS5jb20iLCJhdWQiOiJmaW5la3JhLmNvbSJ9.HHY3hbLrOYh80ej9XTPh_o1OPisBAL2BSqyk-9-SYYM"

        headers = {
            "Content-Type": "application/json"
        }
        ####

        url = "https://finekra-api.sinpas.com.tr/api/Auth/DealerLogin"
        token = "eyJhbGciOiJodHRwOi8vd3d3LnczLm9yZy8yMDAxLzA0L3htbGRzaWctbW9yZSNobWFjLXNoYTI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJiOGZhMmRkMi1jYTkyLWYwMTEtYmY1Yy0wMDBjMjkxNGU5OTkiLCJ1c2VyZW1haWwiOiJ0ZXN0YXBpQHNpbnBhcy5jb20iLCJ1c2VybmFtZSI6IlRlc3QgQXBpIiwidGVuYW50aWQiOiJkMjI0ZDQyMi1iZDNmLWYwMTEtYmY1Yi0wMDBjMjkxNGU5OTkiLCJ0ZW5hbnR1c2VyaWQiOiJiOWZhMmRkMi1jYTkyLWYwMTEtYmY1Yy0wMDBjMjkxNGU5OTkiLCJ0ZW5hbnRuYW1lIjoiVGVrbmlrIFRlc3QgRmlybWFzxLEiLCJuYmYiOjE3NTg2MTg2OTYsImV4cCI6MTc1ODk2NDI5NiwiaXNzIjoiZmluZWtyYS5jb20iLCJhdWQiOiJmaW5la3JhLmNvbSJ9._LQvChO-1SnSzAeECc_niHeCIhHX9_yrRjjpTuZ1GgA"
        # headers = {
        #     "Authorization": f"Bearer {token}"
        # }
        payload = {
            "email": "testapi@sinpas.com",
            "password": "J2Abap8SOw7fBPzS",
            "tenantCode": "1918619137",
            "screenOption": 0
        }
        params = {
			"$count": "true",
			"$skip": "0",
			"$top": "100"
		}

        response = requests.post(url, json=payload, headers=headers)

        print("Status code:", response.status_code)
        print("Response text:", response.text)  # <-- cevabı ekrana bas

        try:
            data = response.json()
        except Exception as e:
            print("JSON decode error:", e)
            return

        # Örneğin token anahtarı 'accessToken' ise:
        token = data.get("accessToken")
        print("Token:", token)
        

        print("done!")