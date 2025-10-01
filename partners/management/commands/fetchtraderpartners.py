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

        all_objs = Partner.objects.select_related().filter()
        all_objs.update(is_commercial=False)

        institutional_objs = Partner.objects.select_related().filter(customer_type="institutional")
        contract_count = 0
        for institutional_obj in institutional_objs:
            contract_count += institutional_obj.partner_contracts.count()
        institutional_objs.update(is_commercial=True)

        print(f"Institutional Count: {len(institutional_objs)}")
        print(f"Total Contract Count: {contract_count}")

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
        contract_count = 0
        for obj in objs:
            contract_count += obj.partner_contracts.count()

        print(f"Individual Count: {len(objs)}")
        print(f"Total Contract Count: {contract_count}")
        print("done!")