from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from compliance.models import *

import pandas as pd
import json
import os
import pyodbc

class Command(BaseCommand):
    help = 'Exports items to JSON file'
    
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

        objs = ThirdPerson.objects.filter(company__id=int(company))

        for obj in objs:
            bank_activities = obj.bank_activities.all()
            for bank_activity in bank_activities:
                bank_activity.third_person_status = obj.status
                bank_activity.save()
                print(f"tp:name: {obj.name} - tp status: {obj.status} - ba status: {bank_activity.third_person_status}")

        print("done!")