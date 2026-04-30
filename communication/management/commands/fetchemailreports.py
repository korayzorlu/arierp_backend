from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from communication.models import *
from communication.tasks import fetch_email_reports_with_setrow_task

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
        parser.add_argument('-c', type=str, required=False, default=None, help='Company to associate with operation')
        parser.add_argument('-t', type=str, required=False, default=None, help='Template to use for email reports')
        parser.add_argument('-d', type=str, required=False, default=None, help='Date to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')
        template = options.get('t')
        date = options.get('d')

        print("processing...")

        params = {
            "company" : company or "0",
            "template" : template or "",
            "date" : date or ""
        }
        
        fetch_email_reports_with_setrow_task.delay(params)
        
        print("done!")