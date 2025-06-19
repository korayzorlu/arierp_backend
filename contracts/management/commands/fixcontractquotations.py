from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *

import pandas as pd
import json
import os

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

        contracts = Contract.objects.select_related("quotation_obj").filter()

        for contract in contracts:
            quotation = Quotation.objects.select_related().filter(code = contract.quotation).first()
            contract.quotation_obj = quotation
            contract.save()
        
        print("done!")