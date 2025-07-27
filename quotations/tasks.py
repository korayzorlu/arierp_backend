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
from decimal import Decimal

from common.models import ImportProcess
from common.utils.common_utils import normalize,safe_decimal
from users.models import User
from .models import *

@shared_task()
def fetch_quick_quotation(company):
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
        SELECT RPR_QUO_ID,
            QUO_HEADER_ID,
            PROJECT_NAME,
            BLOCK_NO,
            FREE_PART_NO,
            LAST_SUB_STATU_NAME,
            GROSS_SALE_AMOUNT_CURR_ID,
            GROSS_SALE_AMOUNT,
            KDV,
            CUSTOMER_SIGN_DATE,
            FREE_PART_DELIVERY_DATE,
            AVERAGE_RETURN_PERIOD,
            TIMESHARE_PERIOD
        FROM RPR_QUO_LIST
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "RPR_QUO_ID" : r.RPR_QUO_ID,
                "QUO_HEADER_ID" : r.QUO_HEADER_ID,
                "PROJECT_NAME" : r.PROJECT_NAME,
                "BLOCK_NO" : r.BLOCK_NO,
                "FREE_PART_NO" : r.FREE_PART_NO,
                "LAST_SUB_STATU_NAME" : r.LAST_SUB_STATU_NAME,
                "GROSS_SALE_AMOUNT_CURR_ID" : r.GROSS_SALE_AMOUNT_CURR_ID,
                "GROSS_SALE_AMOUNT" : r.GROSS_SALE_AMOUNT,
                "KDV" : r.KDV,
                "CUSTOMER_SIGN_DATE" : r.CUSTOMER_SIGN_DATE,
                "FREE_PART_DELIVERY_DATE" : r.FREE_PART_DELIVERY_DATE,
                "AVERAGE_RETURN_PERIOD" : r.AVERAGE_RETURN_PERIOD,
                "TIMESHARE_PERIOD" : r.TIMESHARE_PERIOD,
            }
            for r in records
        ]

        quick_quotations = QuickQuotation.objects.select_related("status","currency","company").all()
        statuses = Status.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        quick_quotation_by_code = {q.code: q for q in quick_quotations if q.code}
        statuses_dict = {s.name: s for s in statuses}
        currencies_dict = {c.code: c for c in currencies}
        

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["RPR_QUO_ID"]):
                obj = (quick_quotation_by_code.get(str(data["RPR_QUO_ID"])))
            else:
                obj = None

            if obj:
                obj.code = str(data["RPR_QUO_ID"]) or ""
                obj.quotation_no = str(data["QUO_HEADER_ID"]) or ""
                obj.project = data["PROJECT_NAME"] or ""
                obj.block = data["BLOCK_NO"] or ""
                obj.unit = data["FREE_PART_NO"] or ""
                obj.status = statuses_dict.get(normalize(data["LAST_SUB_STATU_NAME"]))
                obj.currency = currencies_dict.get("TRY" if data["GROSS_SALE_AMOUNT_CURR_ID"] == "TL" else data["GROSS_SALE_AMOUNT_CURR_ID"])
                obj.price = safe_decimal(data["GROSS_SALE_AMOUNT"])
                obj.vat = safe_decimal(data["KDV"].replace("KDV %","") if data["KDV"] else None)
                obj.customer_signature_date = data["CUSTOMER_SIGN_DATE"].date() if data["CUSTOMER_SIGN_DATE"] else None
                obj.unit_delivery_date = data["FREE_PART_DELIVERY_DATE"].date() if data["FREE_PART_DELIVERY_DATE"] else None
                obj.ortalama_tahsil_suresi = safe_decimal(data["AVERAGE_RETURN_PERIOD"])
                obj.devremulk = data["TIMESHARE_PERIOD"] or ""
                obj.save()
            else:
                print(f"{str(data["RPR_QUO_ID"])} - {data["QUO_HEADER_ID"]}: ")
                QuickQuotation.objects.create(
                    company = company_obj,
                    code = str(data["RPR_QUO_ID"]) or "", 
                    quotation_no = str(data["QUO_HEADER_ID"]) or "",
                    project = data["PROJECT_NAME"] or "",
                    block = data["BLOCK_NO"] or "",
                    unit = data["FREE_PART_NO"] or "",
                    status = statuses_dict.get(normalize(data["LAST_SUB_STATU_NAME"])),
                    currency = currencies_dict.get("TRY" if data["GROSS_SALE_AMOUNT_CURR_ID"] == "TL" else data["GROSS_SALE_AMOUNT_CURR_ID"]),
                    price = safe_decimal(data["GROSS_SALE_AMOUNT"]),
                    vat = safe_decimal(data["KDV"].replace("KDV %","")),
                    customer_signature_date = data["CUSTOMER_SIGN_DATE"].date() if data["CUSTOMER_SIGN_DATE"] else None,
                    unit_delivery_date = data["FREE_PART_DELIVERY_DATE"].date() if data["FREE_PART_DELIVERY_DATE"] else None,
                    ortalama_tahsil_suresi = safe_decimal(data["AVERAGE_RETURN_PERIOD"]),
                    devremulk = data["TIMESHARE_PERIOD"] or "",
                )



        SQL_QUERY = """
        SELECT RPR_QUO_ID,
            CRM_CUSTOMER_ID
        FROM RPR_QUO
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "RPR_QUO_ID" : r.RPR_QUO_ID,
                "CRM_CUSTOMER_ID" : r.CRM_CUSTOMER_ID,
            }
            for r in records
        ]

        quick_quotations = QuickQuotation.objects.select_related().all()
        partners = Partner.objects.select_related().all()

        quick_quotation_by_code = {q.code: q for q in quick_quotations if q.code}
        partners_dict = {p.crm_code: p for p in partners if p.crm_code}

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["RPR_QUO_ID"]):
                obj = (quick_quotation_by_code.get(str(data["RPR_QUO_ID"])))
            else:
                obj = None

            if obj:
                obj.partner = partners_dict.get(str(data["CRM_CUSTOMER_ID"]))
                obj.save()
            else:
                print(f"{str(data["RPR_QUO_ID"])} - {data["CRM_CUSTOMER_ID"]}: ")

    except Exception as e:
        print(e)

@shared_task()
def fetch_quotation(company):
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
        SELECT QuotationHeaderId,
            SubStatuteDefinition,
            CustomerId,
            CurrencyCode,
            LeasingBaseCost,
            CustomerRepresentative,
            RequestDate,
            Vendor,
            Project
        FROM QuotationHeaderLightList
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "QuotationHeaderId" : r.QuotationHeaderId,
                "SubStatuteDefinition" : r.SubStatuteDefinition,
                "CustomerId" : r.CustomerId,
                "CurrencyCode" : r.CurrencyCode,
                "LeasingBaseCost" : r.LeasingBaseCost,
                "CustomerRepresentative" : r.CustomerRepresentative,
                "RequestDate" : r.RequestDate,
                "Vendor" : r.Vendor,
                "Project" : r.Project,
            }
            for r in records
        ]

        quotations = Quotation.objects.select_related("status","currency","company").all()
        statuses = Status.objects.select_related().all()
        partners = Partner.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        quotation_by_code = {q.code: q for q in quotations if q.code}
        statuses_dict = {s.name: s for s in statuses}
        partners_dict = {p.crm_code: p for p in partners}
        currencies_dict = {c.code: c for c in currencies}

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["QuotationHeaderId"]):
                obj = (quotation_by_code.get(str(data["QuotationHeaderId"])))
            else:
                obj = None

            if obj:
                obj.code = str(data["QuotationHeaderId"]) or ""
                obj.status = statuses_dict.get(normalize(data["SubStatuteDefinition"]))
                obj.partner = partners_dict.get(str(data["CustomerId"]))
                obj.currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"])
                obj.kbm = safe_decimal(data["LeasingBaseCost"])
                obj.customer_representative = data["CustomerRepresentative"] or ""
                obj.request_date = data["RequestDate"].date() if data["RequestDate"] else None
                obj.supplier = data["Vendor"] or ""
                obj.project = data["Project"] or ""
                obj.save()
            else:
                print(f"{str(data["QuotationHeaderId"])} - {data["CustomerId"]}: ")
                Quotation.objects.create(
                    company = company_obj,
                    code = str(data["QuotationHeaderId"]) or "",
                    status = statuses_dict.get(normalize(data["SubStatuteDefinition"])),
                    partner = partners_dict.get(str(data["CustomerId"])),
                    currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"]),
                    kbm = safe_decimal(data["LeasingBaseCost"]),
                    customer_representative = data["CustomerRepresentative"] or "",
                    request_date = data["RequestDate"].date() if data["RequestDate"] else None,
                    supplier = data["Vendor"] or "",
                    project = data["Project"] or ""
                )

    except Exception as e:
        print(e)
