from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from django.db.models.functions import Lower,Upper

import pandas as pd
import io
import pyodbc
from datetime import datetime
from sqlalchemy import create_engine
from tqdm import tqdm
import sys

from common.models import ImportProcess
from common.utils.common_utils import normalize
from users.models import User
from .models import *
from leasing.models import Lease

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
def fetch_partners(company):
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
        SELECT FullName,
            FirstName,
            SecondName,
            Surname,
            ContactCompanyName,
            CustomerCode,
            IndividualCustomerId,
            IndividualCustomerCode,
            Phone,
            Address,
            CityName,
            MainSectorId,
            TaxDepartmentName,
            CommercialTaxNo,
            TCIdentityNo,
            TaxAndTCIdentity,
            CountryCode,
            FathersName,
            BirthDate,
            Email,
            PassportNo,
            IS_TURKKEP_CUSTOMER
        FROM CrmIndividualCustomerList
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "FullName" : r.FullName,
                "FirstName" : r.FirstName,
                "SecondName" : r.SecondName,
                "Surname" : r.Surname,
                "ContactCompanyName" : r.ContactCompanyName,
                "CustomerCode" : r.CustomerCode,
                "IndividualCustomerId" : r.IndividualCustomerId,
                "IndividualCustomerCode" : r.IndividualCustomerCode,
                "Phone" : r.Phone,
                "Address" : r.Address,
                "CityName" : r.CityName,
                "MainSectorId" : r.MainSectorId,
                "TaxDepartmentName" : r.TaxDepartmentName,
                "CommercialTaxNo" : r.CommercialTaxNo,
                "TCIdentityNo" : r.TCIdentityNo,
                "TaxAndTCIdentity" : r.TaxAndTCIdentity,
                "CountryCode" : r.CountryCode,
                "FathersName" : r.FathersName,
                "BirthDate" : r.BirthDate,
                "Email" : r.Email,
                "PassportNo" : r.PassportNo or "",
                "IS_TURKKEP_CUSTOMER" : r.IS_TURKKEP_CUSTOMER,
            }
            for r in records
        ]

        # engine = create_engine("mssql+pymssql://lflex:S!gma2014@192.168.82.31:1433/ARI_LEASING")
        # df = pd.read_sql(SQL_QUERY, engine)
        # external_data = df.to_dict(orient="records")

        partners = Partner.objects.select_related("sector","city","country").all()
        sectors = Sector.objects.select_related().all()
        countries = Country.objects.select_related().all()
        cities = City.objects.select_related().all()

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        partner_by_customer = {p.customer_code: p for p in partners if p.customer_code}
        partner_by_name_vkn = {
            (p.name, p.tc_vkn_no): p
            for p in partners
            if p.name and p.tc_vkn_no
        }
        cities_dict = {normalize(c.name): c for c in cities}
        countries_dict = {c.iso2: c for c in countries}
        sectors_dict = {s.main_sector_code: s for s in sectors}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")
                # sys.stdout.write(f"\r%{current_progress} tamamlandı")  # \r ile satır başına dönülür
                # sys.stdout.flush()

            # obj = partners.filter(crm_code = str(data["IndividualCustomerId"])).first()
            # if not obj:
            #     print(f"{str(data["IndividualCustomerId"])} - {data["FullName"]}: ")

            #     if data["BirthDate"]:
            #         birthday = data["BirthDate"].date()
            #     else:
            #         birthday = None
            #     Partner.objects.create(
            #         company = Company.objects.select_related().filter(id = int(company)).first(),
            #         first_name = f"{data["FirstName"]} {data["SecondName"]}" if data["SecondName"] else data["FirstName"] or "",
            #         last_name = data["Surname"] or "",
            #         name = data["FullName"] or "",
            #         formal_name = data["ContactCompanyName"] or "",
            #         customer_code = str(data["CustomerCode"]) or "",
            #         crm_code = str(data["IndividualCustomerId"]) or "",
            #         vat_no = str(data["CommercialTaxNo"]) or "",
            #         vat_office = data["TaxDepartmentName"] or "",
            #         tc_no = str(data["TCIdentityNo"]) or "",
            #         tc_vkn_no = str(data["TaxAndTCIdentity"]) or "",
            #         passport_no = str(data["PassportNo"]) or "",
            #         is_turkkep = True if data["IS_TURKKEP_CUSTOMER"] == "Evet" else False,
            #         sector = sectors.filter(code = str(data["MainSectorId"])).first(),
            #         father_name = data["FathersName"] or "",
            #         birthday = birthday,
            #         country = countries.filter(iso2 = data["CountryCode"]).first(),
            #         city = cities.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            #             Q(lowercase__icontains = data["CityName"] or "xxx") |
            #             Q(uppercase__icontains = data["CityName"] or "xxx")
            #         ).first(),
            #         address = data["Address"] or "",
            #         phone_number = str(data["Phone"]).replace("/","") if data["Phone"] else "",
            #         email = data["Email"] or "",
            #         types = ["customer"]
            #     )

            if str(data["IndividualCustomerId"]):
                obj = (partner_by_crm.get(str(data["IndividualCustomerId"])))
            else:
                obj = None

            if obj:
                obj.customer_code = str(data["CustomerCode"]) or ""
                obj.crm_code = str(data["IndividualCustomerId"]) or ""
                obj.name = data["FullName"] or ""
                obj.first_name = f"{data["FirstName"]} {data["SecondName"]}" if data["SecondName"] else data["FirstName"] or ""
                obj.last_name = data["Surname"] or ""
                obj.formal_name = data["ContactCompanyName"] or ""
                obj.sector = sectors_dict.get(data["MainSectorId"])
                obj.vat_office = data["TaxDepartmentName"] or ""
                obj.vat_no = str(data["CommercialTaxNo"]) or ""
                #obj.phone_number = str(data["Phone"]) if data["Phone"] else ""
                obj.address = data["Address"] or ""
                obj.city = cities_dict.get(normalize(data["CityName"]))
                obj.country = countries_dict.get(data["CountryCode"])
                obj.tc_no = str(data["TCIdentityNo"]) or ""
                obj.tc_vkn_no = str(data["TaxAndTCIdentity"]) or ""
                obj.father_name = data["FathersName"] or ""
                obj.birthday = data["BirthDate"].date() if data["BirthDate"] else None
                obj.email = data["Email"] or ""
                obj.passport_no = str(data["PassportNo"]) or ""
                obj.is_turkkep = True if data["IS_TURKKEP_CUSTOMER"] == "Evet" else False
                obj.save()
            else:
                print(f"{str(data["IndividualCustomerId"])} - {data["FullName"]}: ")
                Partner.objects.create(
                    company = company_obj,
                    first_name = f"{data["FirstName"]} {data["SecondName"]}" if data["SecondName"] else data["FirstName"] or "",
                    last_name = data["Surname"] or "",
                    name = data["FullName"] or "",
                    formal_name = data["ContactCompanyName"] or "",
                    customer_code = str(data["CustomerCode"]) or "",
                    crm_code = str(data["IndividualCustomerId"]) or "",
                    vat_no = str(data["CommercialTaxNo"]) or "",
                    vat_office = data["TaxDepartmentName"] or "",
                    tc_no = str(data["TCIdentityNo"]) or "",
                    tc_vkn_no = str(data["TaxAndTCIdentity"]) or "",
                    passport_no = str(data["PassportNo"]) or "",
                    is_turkkep = True if data["IS_TURKKEP_CUSTOMER"] == "Evet" else False,
                    sector = sectors_dict.get(data["MainSectorId"]),
                    father_name = data["FathersName"] or "",
                    birthday = data["BirthDate"].date() if data["BirthDate"] else None,
                    country = countries_dict.get(data["CountryCode"]),
                    city = cities_dict.get(normalize(data["CityName"])),
                    address = data["Address"] or "",
                    #phone_number = str(data["Phone"]) if data["Phone"] else "",
                    email = data["Email"] or "",
                    types = ["customer"]
                )
    except Exception as e:
        print(e)

@shared_task()
def fetch_partnersi(company):
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
        SELECT InstitutionalCustomerName,
            InstitutionalCustomerId,
            InstitutionalCustomerCode,
            EMail,
            Phone,
            Address,
            CountryName,
            CityName,
            TaxDepartmentName,
            TaxNo
        FROM CrmInstitutionalCustomerList
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "InstitutionalCustomerName" : r.InstitutionalCustomerName,
                "InstitutionalCustomerId" : r.InstitutionalCustomerId,
                "InstitutionalCustomerCode" : r.InstitutionalCustomerCode,
                "EMail" : r.EMail,
                "Phone" : r.Phone,
                "Address" : r.Address,
                "CountryName" : "Turkey" if r.CountryName == "TÜRKİYE" else r.CountryName,
                "CityName" : r.CityName,
                "TaxDepartmentName" : r.TaxDepartmentName,
                "TaxNo" : r.TaxNo
            }
            for r in records
        ]

        # engine = create_engine("mssql+pymssql://lflex:S!gma2014@192.168.82.31:1433/ARI_LEASING")
        # df = pd.read_sql(SQL_QUERY, engine)
        # external_data = df.to_dict(orient="records")

        partners = Partner.objects.select_related("sector","city","country").all()
        countries = Country.objects.select_related().all()
        cities = City.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        partner_by_customer = {p.customer_code: p for p in partners if p.customer_code}
        partner_by_name_vkn = {
            (p.name, p.tc_vkn_no): p
            for p in partners
            if p.name and p.tc_vkn_no
        }
        cities_dict = {normalize(c.name): c for c in cities}
        countries_dict = {c.iso2: c for c in countries}

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            # obj = partners.filter(crm_code = str(data["InstitutionalCustomerId"])).first()
            # if not obj:
            #     print(f"{str(data["InstitutionalCustomerId"])} - {data["InstitutionalCustomerName"]}: ")

            #     Partner.objects.create(
            #         company = company_obj,
            #         name = data["InstitutionalCustomerName"] or "",
            #         formal_name = data["InstitutionalCustomerName"] or "",
            #         customer_code = str(data["InstitutionalCustomerCode"]) or "",
            #         crm_code = str(data["InstitutionalCustomerId"]) or "",
            #         vat_no = str(data["TaxNo"]) or "",
            #         vat_office = data["TaxDepartmentName"] or "",
            #         country = countries.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            #             Q(lowercase__icontains = data["CountryName"] or "xxx") |
            #             Q(uppercase__icontains = data["CountryName"] or "xxx")
            #         ).first(),
            #         city = cities.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            #             Q(lowercase__icontains = data["CityName"] or "xxx") |
            #             Q(uppercase__icontains = data["CityName"] or "xxx")
            #         ).first(),
            #         address = data["Address"] or "",
            #         phone_number = str(data["Phone"]).replace("/","") if data["Phone"] else "",
            #         email = data["EMail"] or "",
            #         types = ["customer"],
            #         customer_type = "institutional"
            #     )

            # obj = (
            #     partner_by_crm.get(str(data["InstitutionalCustomerId"])) or
            #     partner_by_customer.get(str(data["InstitutionalCustomerCode"])) or
            #     partner_by_name_vkn.get((data["InstitutionalCustomerName"], str(data["TaxNo"])))
            # )

            if str(data["InstitutionalCustomerId"]):
                obj = (partner_by_crm.get(str(data["InstitutionalCustomerId"])))
            else:
                obj = None

            if obj:
                obj.customer_code = str(data["InstitutionalCustomerCode"]) or ""
                obj.crm_code = str(data["InstitutionalCustomerId"]) or ""
                obj.name = data["InstitutionalCustomerName"] or ""
                obj.formal_name = data["InstitutionalCustomerName"] or ""
                obj.vat_office = data["TaxDepartmentName"] or ""
                obj.vat_no = str(data["TaxNo"]) or ""
                obj.phone_number = str(data["Phone"]).replace("/","") if data["Phone"] else ""
                obj.address = data["Address"] or ""
                obj.city = cities_dict.get(normalize(data["CityName"]))
                obj.country = countries_dict.get(normalize(data["CountryName"]))
                obj.email = data["EMail"] or ""
                obj.save()
            else:
                print(f"{str(data["InstitutionalCustomerId"])} - {data["InstitutionalCustomerName"]}: ")
                Partner.objects.create(
                    company = company_obj,
                    name = data["InstitutionalCustomerName"] or "",
                    formal_name = data["InstitutionalCustomerName"] or "",
                    customer_code = str(data["InstitutionalCustomerCode"]) or "",
                    crm_code = str(data["InstitutionalCustomerId"]) or "",
                    vat_no = str(data["TaxNo"]) or "",
                    vat_office = data["TaxDepartmentName"] or "",
                    country = countries_dict.get(normalize(data["CountryName"])),
                    city = cities_dict.get(normalize(data["CityName"])),
                    address = data["Address"] or "",
                    phone_number = str(data["Phone"]).replace("/","") if data["Phone"] else "",
                    email = data["EMail"] or "",
                    types = ["customer"],
                    customer_type = "institutional"
                )
    except Exception as e:
        print(e)

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
def fetch_phone_numbers_bireysel(company):
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
            SELECT 
                cw.CustomerId,
                cw.CustomerName,
                com.CommunicationValue
            FROM dbo.CrmCustomerWithTypesLight cw
            LEFT JOIN dbo.CrmContact cc 
                ON cw.CONTACTID = cc.ContactId
            LEFT JOIN dbo.CrmAddress ad 
                ON ad.ObjectId = cc.ContactId
            LEFT JOIN dbo.CrmAddressCommunicationInformation com 
                ON com.AddressId = ad.AddressId
            LEFT JOIN dbo.LeasingOperationProject lop 
                ON cw.CustomerId = lop.CustomerId
            WHERE ad.AddressTypeId = 4
            AND com.CommunicationType IN (5,6)
            AND lop.RiskIncludingTypeId NOT IN (3,8,9,4)
            GROUP BY 
                cw.CustomerId,
                cw.CustomerName,
                com.CommunicationValue
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "CustomerId" : r.CustomerId,
                "CommunicationValue" : r.CommunicationValue,
            }
            for r in records
        ]

        partners = Partner.objects.select_related().all()

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["CustomerId"]):
                obj = (partner_by_crm.get(str(data["CustomerId"])))
            else:
                obj = None

            if obj:
                obj.phone_number = str(data["CommunicationValue"]) or ""
                obj.save()

    except Exception as e:
        print(e)

@shared_task()
def fetch_phone_numbers_tuzel(company):
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
            SELECT 
                cw.CustomerId,
                cw.CustomerName,
                com.CommunicationValue
            FROM dbo.CrmCustomerWithTypesLight cw
            LEFT JOIN dbo.CrmAddress ad 
                ON ad.ObjectId = cw.CustomerId
            LEFT JOIN dbo.CrmAddressCommunicationInformation com 
                ON com.AddressId = ad.AddressId
            LEFT JOIN dbo.LeasingOperationProject lop 
                ON cw.CustomerId = lop.CustomerId
            WHERE ad.AddressTypeId = 2
            AND com.CommunicationType IN (5,6)
            AND lop.RiskIncludingTypeId NOT IN (3,8,9,4)
            GROUP BY 
                cw.CustomerId,
                cw.CustomerName,
                com.CommunicationValue

        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "CustomerId" : r.CustomerId,
                "CommunicationValue" : r.CommunicationValue,
            }
            for r in records
        ]

        partners = Partner.objects.select_related().all()

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["CustomerId"]):
                obj = (partner_by_crm.get(str(data["CustomerId"])))
            else:
                obj = None

            if obj:
                obj.phone_number = str(data["CommunicationValue"]) or ""
                obj.save()

    except Exception as e:
        print(e)