from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *

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
        
        base_path = os.path.join(os.getcwd(), "media", "docs")

        objs = Lease.objects.select_related("contract","contract__quotation_obj","contract__quotation_obj__partner").filter()

        data = {
            "Kira Planı No": [],
            "Sözleşme No": [],
            "Müşteri Kodu": [],
            "Müşteri Adı": [],
            "Müşteri TC": []
        }

        

        for obj in objs:

            data["Kira Planı No"].append(obj.code)
            data["Sözleşme No"].append(obj.contract.code)
            data["Müşteri Kodu"].append(obj.contract.quotation_obj.partner.customer_code if obj.contract.quotation_obj.partner else "")
            data["Müşteri Adı"].append(obj.contract.quotation_obj.partner.name if obj.contract.quotation_obj.partner else "")
            data["Müşteri TC"].append(obj.contract.quotation_obj.partner.tc_vkn_no if obj.contract.quotation_obj.partner else "")
        
        df = pd.DataFrame(data)

        excel_dosyasi_adi = "sozlesmeler.xlsx"
        with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Sözleşmeler', index=False)
        
        print("done!")