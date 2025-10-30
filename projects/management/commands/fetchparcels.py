from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from projects.models import *
from projects.tasks import fetch_parcels, fetch_projects

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
        
        fetch_parcels.delay(company)

        print("done!")