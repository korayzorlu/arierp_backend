from django.conf import settings
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.core.mail import EmailMessage, send_mail

import pyodbc
import os
import traceback
import logging
from datetime import datetime

from common.utils.common_utils import normalize,safe_decimal
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from partners.models import *

def fetch_partners_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "partners","sql","bireysel_musteriler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        # engine = create_engine("mssql+pymssql://lflex:S!gma2014@192.168.82.31:1433/ARI_LEASING")
        # df = pd.read_sql(SQL_QUERY, engine)
        # external_data = df.to_dict(orient="records")

        partners = Partner.objects.select_related("sector","city","country").filter(company__id=int(company))
        sectors = Sector.objects.select_related().filter(company__id=int(company))
        countries = Country.objects.select_related().all()
        cities = City.objects.select_related().all()

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        # partner_by_customer = {p.customer_code: p for p in partners if p.customer_code}
        # partner_by_name_vkn = {
        #     (p.name, p.tc_vkn_no): p
        #     for p in partners
        #     if p.name and p.tc_vkn_no
        # }
        cities_dict = {normalize(c.name): c for c in cities}
        countries_dict = {c.iso2: c for c in countries}
        sectors_dict = {s.main_sector_code: s for s in sectors}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        #BATCH_SIZE = 1000
        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            # previous_progress = 0
            for index,data in enumerate(records):
                # current_progress = ((index + 1)/len(records))*100

                # if current_progress - previous_progress >= 1:
                #     previous_progress = current_progress
                #     print(f"{int(current_progress)} %")

                if str(data.IndividualCustomerId):
                    obj = (partner_by_crm.get(str(data.IndividualCustomerId)))
                else:
                    obj = None

                if obj:
                    obj.customer_code = str(data.CustomerCode) or ""
                    obj.crm_code = str(data.IndividualCustomerId) or ""
                    obj.name = data.FullName or ""
                    obj.first_name = f"{data.FirstName} {data.SecondName}" if data.SecondName else data.FirstName or ""
                    obj.last_name = data.Surname or ""
                    obj.formal_name = data.ContactCompanyName or ""
                    obj.sector = sectors_dict.get(data.MainSectorId)
                    obj.vat_office = data.TaxDepartmentName or ""
                    obj.vat_no = str(data.CommercialTaxNo) or ""
                    #obj.phone_number = str(data["Phone"]) if data["Phone"] else ""
                    obj.address = data.Address or ""
                    obj.city = cities_dict.get(normalize(data.CityName))
                    obj.country = countries_dict.get(data.CountryCode)
                    obj.tc_no = str(data.TCIdentityNo) or ""
                    obj.tc_vkn_no = str(data.TaxAndTCIdentity) or ""
                    obj.father_name = data.FathersName or ""
                    obj.birthday = data.BirthDate.date() if data.BirthDate else None
                    obj.birth_place = data.BirthPlace or ""
                    obj.email = data.Email or ""
                    obj.passport_no = str(data.PassportNo) or ""
                    obj.is_turkkep = True if data.IS_TURKKEP_CUSTOMER == "Evet" else False
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    #print(f"{str(data.IndividualCustomerId)} - {data.FullName}: ")
                    create_objs.append(Partner(
                        company = company_obj,
                        first_name = f"{data.FirstName} {data.SecondName}" if data.SecondName else data.FirstName or "",
                        last_name = data.Surname or "",
                        name = data.FullName or "",
                        formal_name = data.ContactCompanyName or "",
                        customer_code = str(data.CustomerCode) or "",
                        crm_code = str(data.IndividualCustomerId) or "",
                        vat_no = str(data.CommercialTaxNo) or "",
                        vat_office = data.TaxDepartmentName or "",
                        tc_no = str(data.TCIdentityNo) or "",
                        tc_vkn_no = str(data.TaxAndTCIdentity) or "",
                        passport_no = str(data.PassportNo) or "",
                        is_turkkep = True if data.IS_TURKKEP_CUSTOMER == "Evet" else False,
                        sector = sectors_dict.get(data.MainSectorId),
                        father_name = data.FathersName or "",
                        birthday = data.BirthDate.date() if data.BirthDate else None,
                        birth_place = data.BirthPlace or "",
                        country = countries_dict.get(data.CountryCode),
                        city = cities_dict.get(normalize(data.CityName)),
                        address = data.Address or "",
                        #phone_number = str(data["Phone"]) if data["Phone"] else "",
                        email = data.Email or "",
                        types = ["customer"]
                    ))
                    create_progress += 1

            if update_objs:
                Partner.objects.bulk_update(update_objs, [
                    "customer_code",
                    "crm_code",
                    "name",
                    "first_name",
                    "last_name",
                    "formal_name",
                    "sector",
                    "vat_office",
                    "vat_no",
                    "address",
                    "city",
                    "country",
                    "tc_no",
                    "tc_vkn_no",
                    "father_name",
                    "birthday",
                    "birth_place",
                    "email",
                    "passport_no",
                    "is_turkkep",
                ], batch_size=BATCH_SIZE)
                # print(f"{len(update_objs)} kayıt güncellendi.")
            if create_objs:
                Partner.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
                # print(f"{len(create_objs)} kayıt oluşturuldu.")

            # BATCH_SIZE = 1000

            # for i, update_obj in enumerate(update_objs, start=1):
            #     Partner.objects.filter(id=update_obj.id).update(
            #         customer_code=update_obj.customer_code,
            #         crm_code=update_obj.crm_code,
            #         name=update_obj.name,
            #         first_name=update_obj.first_name,
            #         last_name=update_obj.last_name,
            #         formal_name=update_obj.formal_name,
            #         sector=update_obj.sector,
            #         vat_office=update_obj.vat_office,
            #         vat_no=update_obj.vat_no,
            #         address=update_obj.address,
            #         city=update_obj.city,
            #         country=update_obj.country,
            #         tc_no=update_obj.tc_no,
            #         tc_vkn_no=update_obj.tc_vkn_no,
            #         father_name=update_obj.father_name,
            #         birthday=update_obj.birthday,
            #         email=update_obj.email,
            #         passport_no=update_obj.passport_no,
            #         is_turkkep=update_obj.is_turkkep,
            #     )

            #     if i % BATCH_SIZE == 0:
            #         print(f"{i} kayıt güncellendi...")
            # print(f"Toplam {len(update_objs)} kayıt güncellendi.")

            # BATCH_SIZE = 1000

            # for i in range(0, len(create_objs), BATCH_SIZE):
            #     batch = create_objs[i:i+BATCH_SIZE]
            #     Partner.objects.bulk_create(batch, batch_size=BATCH_SIZE)
            #     print(f"{i + len(batch)}/{len(create_objs)} kayıt oluşturuldu.")

            # print(f"Toplam {len(create_objs)} kayıt oluşturuldu.")
        print(f"Toplam {update_progress} bireysel partner güncellendi.")
        print(f"Toplam {create_progress} bireysel partner oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)

def fetch_partnersi_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "partners","sql","tuzel_musteriler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        partners = Partner.objects.select_related("sector","city","country").filter(company__id=int(company))
        countries = Country.objects.select_related().all()
        cities = City.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        cities_dict = {normalize(c.name): c for c in cities}
        countries_dict = {c.iso2: c for c in countries}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):

                if str(data.InstitutionalCustomerId):
                    obj = (partner_by_crm.get(str(data.InstitutionalCustomerId)))
                else:
                    obj = None

                if obj:
                    obj.customer_code = str(data.InstitutionalCustomerCode) or ""
                    obj.crm_code = str(data.InstitutionalCustomerId) or ""
                    obj.name = data.InstitutionalCustomerName or ""
                    obj.formal_name = data.InstitutionalCustomerName or ""
                    obj.vat_office = data.TaxDepartmentName or ""
                    obj.vat_no = str(data.TaxNo) or ""
                    obj.phone_number = str(data.Phone).replace("/","") if data.Phone else ""
                    obj.address = data.Address or ""
                    obj.city = cities_dict.get(normalize(data.CityName))
                    obj.country = countries_dict.get(normalize(data.CountryName))
                    obj.email = data.EMail or ""
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    print(f"{str(data.InstitutionalCustomerId)} - {data.InstitutionalCustomerName}: ")
                    create_objs.append(Partner(
                        company = company_obj,
                        name = data.InstitutionalCustomerName or "",
                        formal_name = data.InstitutionalCustomerName or "",
                        customer_code = str(data.InstitutionalCustomerCode) or "",
                        crm_code = str(data.InstitutionalCustomerId) or "",
                        vat_no = str(data.TaxNo) or "",
                        vat_office = data.TaxDepartmentName or "",
                        country = countries_dict.get(normalize(data.CountryName)),
                        city = cities_dict.get(normalize(data.CityName)),
                        address = data.Address or "",
                        phone_number = str(data.Phone).replace("/","") if data.Phone else "",
                        email = data.EMail or "",
                        types = ["customer"],
                        customer_type = "institutional"
                    ))
                    create_progress += 1
            if update_objs:
                Partner.objects.bulk_update(update_objs, [
                    "customer_code",
                    "crm_code",
                    "name",
                    "formal_name",
                    "vat_office",
                    "vat_no",
                    "phone_number",
                    "address",
                    "city",
                    "country",
                    "email",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Partner.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} tüzel partner güncellendi.")
        print(f"Toplam {create_progress} tüzel partner oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)

def fetch_phone_numbers_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "partners","sql","bireysel_telefon_numaralari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        partners = Partner.objects.select_related().filter(company__id=int(company))

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        update_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []

            for index,data in enumerate(records):
                if str(data.CustomerId):
                    obj = (partner_by_crm.get(str(data.CustomerId)))
                else:
                    obj = None

                if obj:
                    obj.phone_number = str(data.CommunicationValue) or ""
                    update_objs.append(obj)
                    update_progress += 1

            if update_objs:
                Partner.objects.bulk_update(update_objs, [
                    "phone_number",
                ], batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} bireysel partner telefon numarası güncellendi.")
        print("--------")
    except Exception as e:
        print(e)

def fetch_phone_numbersi_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "partners","sql","tuzel_telefon_numaralari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        partners = Partner.objects.select_related().filter(company__id=int(company))

        partner_by_crm = {p.crm_code: p for p in partners if p.crm_code}

        update_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break

            update_objs = []
            for index,data in enumerate(records):
                if str(data.CustomerId):
                    obj = (partner_by_crm.get(str(data.CustomerId)))
                else:
                    obj = None

                if obj:
                    obj.phone_number = str(data.CommunicationValue) or ""
                    update_objs.append(obj)
                    update_progress += 1

            if update_objs:
                Partner.objects.bulk_update(update_objs, [
                    "phone_number",
                ], batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} tüzel partner telefon numarası güncellendi.")
        print("--------")
    except Exception as e:
        print(e)

def fetch_partner_advances_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "partners","sql","musteri_avanslari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        partners = Partner.objects.select_related().filter(company_id=int(company))
        partners.update(advance_amount=0)

        partner_by_code = {p.crm_code: p for p in partners if p.crm_code}
        
        update_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            for index,data in enumerate(records):
                if str(data.TrnAccountCrmId):
                    obj = (partner_by_code.get(str(data.TrnAccountCrmId)))
                else:
                    obj = None

                if obj:
                    obj.advance_amount = safe_decimal(data.TrnAmountLocal)
                    obj.save()
                    update_objs.append(obj)
                    update_progress += 1

            if update_objs:
                Partner.objects.bulk_update(update_objs, [
                    "advance_amount",
                ], batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} müşteri avansı güncellendi.")
        print("--------")
    except Exception as e:
        traceback.print_exc()

def send_warning_email_for_ignored_partners(params):
    today = datetime.today().date().strftime("%d.%m.%Y")

    def send_outlook_email(subject, message, from_email, recipient_list, attachments=None):
        email = EmailMessage(
            subject,
            message,
            from_email,
            recipient_list,
        )
        if attachments:
            for attachment in attachments:
                email.attach(attachment['name'], attachment['content'], attachment['mimetype'])
        email.send(fail_silently=False)
        #send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            
    subject = 'YASAKLI MÜŞTERİ İÇİN İŞLEM BİLDİRİMİ'
    message = f'''
        Aşağıdaki kişi/kurum için sistem üzerinde işlem yapılmak istendi ancak bu kişi/kurum yasaklı listesinde bulunduğu için işlemleri kısıtlanmıştır.

        Kişi/Kurum Bilgileri:
            Tarih: {today}
            İsim: {params.get('name','')}
            TC/VKN No: {params.get('tc_vkn_no','')}
            CRM Kodu: {params.get('crm_code','')}

        İşlemi yapan kullanıcı:
            İsim: {params.get('request_user_full_name','')}
            Email: {params.get('request_user_email','')}

    '''
    from_email = 'Arınet <noreply@arileasing.com.tr>'
    recipient_list = settings.IGNORED_PARTNER_EMAIL_LIST

    send_outlook_email(subject, message, from_email, recipient_list)