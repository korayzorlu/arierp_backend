from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import Q

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict

from .models import *
from partners.models import Partner
from leasing.models import BankActivity
from .utils.third_person_utils import check_third_person_in_partners,fix_third_person_bank_activity_date

@shared_task()
def fetch_black_list_partners(company):
    excel_file = pd.ExcelFile("files/black-list.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/black-list.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    #BlackListPerson.objects.select_related().all().delete()
    company_obj = Company.objects.select_related().filter(id=int(company)).first()

    previous_progress = 0
    old_obj_count = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        if not BlackListPerson.objects.filter(tc_vkn_passport_no__icontains=str(row['TC/VKN/Pasaport No']), company=company_obj).exists():
            BlackListPerson.objects.create(
                company = company_obj,
                name = str(row['İsim / Ünvan']) if not pd.isna(row['İsim / Ünvan']) else "",
                tc_vkn_passport_no = str(row['TC/VKN/Pasaport No']) if not pd.isna(row['TC/VKN/Pasaport No']) else "",
                other_names = str(row['Bilinen Diğer İsimler']) if not pd.isna(row['Bilinen Diğer İsimler']) else "",
                nationality = str(row['Uyruğu']) if not pd.isna(row['Uyruğu']) else "",
                birthday = str(row['Doğum Tarihi']) if not pd.isna(row['Doğum Tarihi']) else "",
                organization = str(row['Örgüt']) if not pd.isna(row['Örgüt']) else "",
                date_number = str(row['Resmi Gazete Tarih ve Sayısı']) if not pd.isna(row['Resmi Gazete Tarih ve Sayısı']) else "",
            )
        else:
            print(f"BlackListPerson with TC/VKN/Pasaport No {str(row['TC/VKN/Pasaport No'])} already exists.")
        
    print(f"{old_obj_count} objects updated for leases.")

@shared_task()
def update_ignored_partners(company):
    partner_objs = Partner.objects.select_related().all()

    previous_progress = 0
    old_obj_count = 0
    for index,obj in enumerate(partner_objs):
        current_progress = ((index + 1)/len(partner_objs))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        if obj.tc_vkn_no is not None:
            if BlackListPerson.objects.select_related().filter(tc_vkn_passport_no__icontains = obj.tc_vkn_no).exists():
                print(f"Yasaklı müşteri algılandı: {obj.tc_vkn_no} - {obj.name}")
        
    print(f"{old_obj_count} objects updated for partners.")

@shared_task()
def check_third_person_in_partnerss(company):
    check_third_person_in_partners(company)

@shared_task()
def fix_third_person_bank_activity_datee(company):
    fix_third_person_bank_activity_date(company)