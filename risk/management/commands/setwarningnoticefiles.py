from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *
from risk.tasks import set_warning_notice_files_task

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
        parser.add_argument('-r', action='store_true', default=False, help='Reset flag for operation')

    def handle(self, *args, **options):
        company = options.get('c')
        reset = options.get('r')

        print("processing...")
        
        set_warning_notice_files_task.delay(company, reset)
        
        print("done!")