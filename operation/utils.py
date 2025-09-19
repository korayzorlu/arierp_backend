from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value,OuterRef,Subquery

from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
import re
import os
import random
import string

from .models import *

def export_partner_advance_activities(self):
    objs = PartnerAdvanceActivityLease.objects.select_related().filter(leaseflex_automation = True).order_by("partner_advance_activity__partner__name","-id")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Sözleşme No": [],
        "Müşteri": [],
        "TC/VKN No": [],
        "İşlenen Tutar": [],
        "PB": [],
        "İşlem Tarihi": [],
    }

    previous_progress = 0
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Sözleşme No"].append(obj.lease.contract.code if obj.lease and obj.lease.contract else "")
        data["Müşteri"].append(obj.partner_advance_activity.partner.name if obj.partner_advance_activity and obj.partner_advance_activity.partner else "")
        data["TC/VKN No"].append(obj.partner_advance_activity.partner.tc_vkn_no if obj.partner_advance_activity and obj.partner_advance_activity.partner else "")
        data["İşlenen Tutar"].append(obj.processed_amount if obj.processed_amount is not None else 0)
        data["PB"].append(obj.partner_advance_activity.currency.code if obj.partner_advance_activity and obj.partner_advance_activity.currency else "")
        data["İşlem Tarihi"].append(datetime.today().strftime("%y%m%d"))

    df = pd.DataFrame(data)
    # df = df.drop_duplicates()
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "operation", "partner_advance_activities", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    karakterler = string.ascii_letters + string.digits
    rastgele_deger = ''.join(random.choices(karakterler, k=8))

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-müşteri-avansları.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Müşteri Avansları', index=False)
        

    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()
