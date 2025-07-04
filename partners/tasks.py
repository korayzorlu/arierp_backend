from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import pandas as pd
import io
import pyodbc

from common.models import ImportProcess
from users.models import User
from .models import *

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
def fix_partners(company):
    SERVER = "192.168.81.8,1433"
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