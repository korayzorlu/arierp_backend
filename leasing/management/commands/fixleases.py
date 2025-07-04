from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from leasing.models import *
from leasing.tasks import *
from leasing.models import *

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
        parser.add_argument('-l', type=str, help='Lease to associate with operation')

    def handle(self, *args, **options):
        lease_code = options.get('l')

        print("processing...")

        if lease_code == "0":
            objs = Lease.objects.select_related().filter()
            previous_progress = 0
            for index,obj in enumerate(objs):
                current_progress = ((index + 1)/len(objs))*100

                if current_progress - previous_progress >= 5:
                    print(current_progress)
                    previous_progress = current_progress

                fix_leases.delay(obj.code)
        else:
            fix_leases.delay(lease_code)
        
        print("done!")