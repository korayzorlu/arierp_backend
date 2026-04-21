from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from django.db.models.functions import Lower,Upper
from django.conf import settings

import pandas as pd
import io
import pyodbc
from datetime import datetime
from sqlalchemy import create_engine
from tqdm import tqdm
import sys
import os

from common.models import ImportProcess
from common.utils.common_utils import normalize
from users.models import User
from .models import *
from leasing.models import Lease
from .utils.partner_utils import *
from .utils.sgk_job_utils import fetch_sgk_jobs_from_leaseflex
from compliance.utils.third_person_utils import check_third_person_in_partners

#tekrar eden düzeltme
# from django.db.models import Max
# from django.db.models import Count
# objs=(Partner.objects.exclude(crm_code__isnull=True).values('crm_code').annotate(count=Count('id')).filter(count__gt=1).values_list('crm_code',flat=True))
# objs_to_delete=(Partner.objects.filter(crm_code__in=objs).values('crm_code').annotate(latest_id=Max('id')).values_list('latest_id',flat=True))
# Partner.objects.filter(id__in=objs_to_delete).delete()


def sendAlert(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'public_room',
        {
            "type": "send_alert",
            "message": message,
        }
    )

@shared_task(bind=True)
def importPartners(self,df_json,user_id):
    #process = ImportProcess.objects.filter(model_name="Partner",user__id=user_id,task_id=self.request.id)
    user = User.objects.filter(id = user_id).first()
    process = ImportProcess.objects.create(
            user = user,
            model_name = "Partner",
            task_id = self.request.id,
            status = "in_progress"
        )
    process.save()

    # if not process:
    #     return {"error": "Process not found!"}
    
    df = pd.read_json(io.StringIO(df_json), orient='records')

    for index,row in df.iterrows():
        if pd.isnull(row["name"]) or row["name"] == "":
            process.status = "rejected"
            process.save()
            process.delete()
            return
        
        print(row["name"])

    process.status = "completed"
    process.save()
        
@shared_task()
def fix_partnerss(company):
    SERVER = "192.168.82.31,1433"
    DATABASE = "ARI_LEASING"
    USERNAME = "lflex"
    PASSWORD = "S!gma2014"

    connectionString = f'''
        DRIVER={{ODBC Driver 18 for SQL Server}};
        SERVER={SERVER};
        DATABASE={DATABASE};
        UID={USERNAME};
        PWD={PASSWORD};
        Provider=SQLNCLI11;
        Integrated Security=SSPI;
        Persist Security Info=False;
        Initial Catalog=MASTER;
        TrustServerCertificate=yes;
    '''

    try:
        conn = pyodbc.connect(connectionString)
        
        SQL_QUERY = """
        SELECT *
        FROM TradeAccount
        ORDER BY AccId
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()
        external_data=[
            {   
                "customer_code" : r.CustomerId,
                "crm_code" : r.CustomerCode,
                "name" : r.CustomerName,
                "first_name" : r.FirstName,
                "last_name" : r.Surname,
            }
            for r in records
        ]

        for data in external_data:
            if Partner.objects.select_related().filter(crm_code = str(int(data["crm_code"]))).exists():
                obj = Partner.objects.select_related().filter(crm_code = str(int(data["crm_code"]))).first()
                try:
                    obj.customer_code = str(int(data["customer_code"]))
                    obj.save()
                except:
                    obj.customer_code = None
                    obj.save()
            elif Partner.objects.select_related().filter(customer_code = str(int(data["customer_code"]))).exists():
                obj = Partner.objects.select_related().filter(crm_code = str(int(data["customer_code"]))).first()
                obj.crm_code = str(int(data["crm_code"]))
                obj.save()
            elif Partner.objects.select_related().filter(name = str(int(data["name"])), tc_vkn_no=str(int(data["name"]))).exists():
                obj = Partner.objects.select_related().filter(name = str(int(data["name"])), tc_vkn_no=str(int(data["name"]))).first()
                obj.crm_code = str(int(data["crm_code"]))
                obj.save()
                try:
                    obj.customer_code = str(int(data["customer_code"]))
                    obj.save()
                except:
                    obj.customer_code = None
                    obj.save()
            else:
                obj = Partner.objects.create(
                    company = Company.objects.select_related().filter(id = int(company)).first(),
                    first_name = data["first_name"] if not pd.isna(data["first_name"]) else None,
                    last_name = data["last_name"] if not pd.isna(data["last_name"]) else None,
                    name = data["name"] if not pd.isna(data["name"]) else None,
                    formal_name = data["name"] if not pd.isna(data["name"]) else None,
                    customer_code = str(int(data["customer_code"])) if not pd.isna(data["customer_code"]) else None,
                    crm_code = str(int(data["crm_code"])),
                    vat_no = str(data["customer_code"]) if not pd.isna(data["customer_code"]) else None,
                    vat_office = row.get("Vergi Dairesi") or None,
                    tc_no = row["TC Kimlik No"],
                    tc_vkn_no = row["Vergi/TC Kimlik No"],
                    passport_no = row["Pasaport No"],
                    ticari_sicil_no = row["Ticari Sicil No"],
                    kep = row["Kep Adresi"],
                    kep_expiry_date = kep_expiry_date,
                    is_turkkep = True if row["Türkkep Müşterisi Mi ?"] == "Evet" else False,
                    sector = Sector.objects.filter(code = str(row["Ana Faaliyet Sektör Adı"])).first(),
                    father_name = row["Baba Adı"],
                    birthday = birthday,
                    country = Country.objects.filter(iso2 = row["Ülke Kodu"]).first(),
                    city = City.objects.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = row["Şehir Adı"] or "xxx") | Q(uppercase__icontains = row["Şehir Adı"] or "xxx")).first(),
                    address = row["Adres"][:250] if row["Adres"] else None,
                    phone_number = row.get("Telefon") or None,
                    email = row.get("Email") or None,
                    types = ["customer"]
                )
                obj.save()
    except Exception as e:
        print(e)
@shared_task()
def fetch_partner_advances(company):
    fetch_partner_advances_from_leaseflex(company)

@shared_task()
def fetch_partners(company):
    fetch_partners_from_leaseflex(company)
    fetch_partnersi_from_leaseflex(company)
    fetch_phone_numbers_from_leaseflex(company)
    fetch_phone_numbersi_from_leaseflex(company)
    fetch_partner_advances_from_leaseflex(company)
    check_third_person_in_partners(company)

@shared_task()
def fetch_special_partners(company):
    excel_file = pd.ExcelFile("files/ozel-musteriler.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/ozel-musteriler.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    for index,row in df.iterrows():
        special_partners = Partner.objects.select_related().filter(types__contains=["special"])
        for special_partner in special_partners:
            special_partner.types.remove('special')
            special_partner.save()
        objs = Partner.objects.select_related().annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            Q(lowercase__icontains = row['MÜŞTERİ ADI']) |
            Q(uppercase__icontains = row['MÜŞTERİ ADI'])
        )
        if objs:
            if len(objs) == 1:
                for obj in objs:
                    if row['Arayacak Kişi'] == "ÖZEL MÜŞTERİ":
                        obj.types = ["customer","special"]
                    elif row['Arayacak Kişi'] == "BARTER":
                        obj.types = ["customer","barter"]
                    elif row['Arayacak Kişi'] == "VİRMAN":
                        obj.types = ["customer","virman"]
                    obj.save()
            else:
                print(f"{row['MÜŞTERİ ADI']} için bulunanlar;")
                for obj in objs:
                    print(f"....{obj.name} - {obj.tc_vkn_no}")

@shared_task()
def fetch_phone_numbers(company):
    excel_file = pd.ExcelFile("files/musteri-tel-no.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/musteri-tel-no.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    leases = Lease.objects.select_related("contract__partner").all()

    lease_by_code = {l.code: l for l in leases if l.code}

    previous_progress = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        obj = (lease_by_code.get(str(row["OperationProjectCode"])))

        if obj:
            partner = obj.contract.partner
            if partner and not pd.isna(row['CommunicationValue']):
                partner.phone_number = str(row['CommunicationValue'])
                partner.save()

    excel_file = pd.ExcelFile("files/musteri-tel-no.xlsx")
    sheet_name = excel_file.sheet_names[1]

    file_data = pd.read_excel("files/musteri-tel-no.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    partners = Partner.objects.select_related().all()

    partner_by_code = {l.crm_code: l for l in partners if l.crm_code}

    previous_progress = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        obj = (partner_by_code.get(str(row["CustomerId"])))

        if obj:
            if not pd.isna(row['Phone']):
                obj.phone_number = str(row['Phone']) if not pd.isna(row['Phone']) else ""
                obj.save()
            if not pd.isna(row['Email']):
                obj.email = str(row['Email']) if not pd.isna(row['Email']) else ""
                obj.save()

@shared_task()
def set_partner_scores_task(company, partner=None):
    set_partner_scores(company, partner)

@shared_task()
def fetch_sgk_jobs(company):
    fetch_sgk_jobs_from_leaseflex(company)