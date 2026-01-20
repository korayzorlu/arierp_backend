from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *
from leasing.tasks import get_lease_delay_task

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
        parser.add_argument('-l', type=str, help='Lease to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')
        lease_id = options.get('l')

        print("processing...")
        
        get_lease_delay_task.delay(company, lease_id)
        
        print("done!")