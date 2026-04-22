from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

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
        parser.add_argument('-g', type=str, help='Group ID to associate with operation')
        parser.add_argument('-e', type=str, help='Email to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')
        group_id = options.get('g')
        email = options.get('e')

        print("processing...")
        
        url = "https://rest.setrow.com/email/add"

        headers = {
            "Authorization": f"Bearer {settings.SETROW_API_KEY}",
        }
        payload = {
            "email": email,
            "groupId": group_id
        }
        response = requests.post(url, headers=headers, json=[payload])
        print(response.status_code, response.json())
        
        print("done!")