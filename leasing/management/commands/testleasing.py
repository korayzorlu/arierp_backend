from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os
from bs4 import BeautifulSoup

from leasing.models import Lease,Installment

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

        installments = Installment.objects.select_related("lease").filter(lease__lease_id="73745")

        installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency is not None}
        
        obj = (installment_by_code.get(("73745",int(0))))

        print(f"{obj.sequency} - {obj.payment_date} - {obj.amount}")


        
        print("done!")