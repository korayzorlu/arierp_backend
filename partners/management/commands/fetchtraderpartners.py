from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Count, F, Func, Value, CharField

from contracts.models import *
from leasing.models import *
from partners.tasks import fetch_partners
from partners.models import *

import pandas as pd
import json
import os
import pyodbc

class CodePrefix(Func):
    function = 'SPLIT_PART'
    template = "%(function)s(%(expressions)s, '/', 1)"
    output_field = CharField()

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
        
        # objs = Partner.objects.select_related().annotate(
        #     contract_count=Count('partner_contracts')
        # ).filter(
        #     customer_type="institutional",
        #     contract_count__gt=1
        # )

        #objs = Partner.objects.select_related().filter(customer_type="institutional")

        

        objs = Partner.objects.select_related().annotate(
            unique_contract_count=Count(
                CodePrefix('partner_contracts__code'),
                distinct=True
            )
        ).filter(
            customer_type="individual",
            unique_contract_count__gt=1
        )

        objs.update(is_commercial=True)

        print(len(objs))
        
        print("done!")