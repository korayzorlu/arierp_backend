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
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner

@shared_task()
def fetch_projects(company):
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
        SELECT PROJECT_ID,
            PROJECT_NAME,
            VENDOR_ID,
            COMMISSION_RATE,
            TERM_DIFF_RATE
        FROM RPR_PROJECT
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {   
                "PROJECT_ID" : r.PROJECT_ID,
                "PROJECT_NAME" : r.PROJECT_NAME,
                "VENDOR_ID" : r.VENDOR_ID,
                "COMMISSION_RATE" : r.COMMISSION_RATE,
                "TERM_DIFF_RATE" : r.TERM_DIFF_RATE,
            }
            for r in records
        ]

        projects = Project.objects.select_related("company","partner").all()
        partners = Partner.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        project_by_code = {p.project_id: p for p in projects if p.project_id}
        partners_dict = {p.crm_code: p for p in partners}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["PROJECT_ID"]):
                obj = (project_by_code.get(str(data["PROJECT_ID"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.project_id = str(data["PROJECT_ID"]) or ""
                obj.name = str(data["PROJECT_NAME"]) or ""
                obj.partner = partners_dict.get(str(data["VENDOR_ID"]))
                obj.comission_rate = safe_decimal(data["COMMISSION_RATE"])
                obj.term_diff_rate = safe_decimal(data["TERM_DIFF_RATE"])
                obj.save()
            else:
                new_obj_count += 1
                Project.objects.create(
                    company = company_obj,
                    project_id = str(data["PROJECT_ID"]) or "",
                    name = str(data["PROJECT_NAME"]) or "",
                    partner = partners_dict.get(str(data["VENDOR_ID"])),
                    comission_rate = safe_decimal(data["COMMISSION_RATE"]),
                    term_diff_rate = safe_decimal(data["TERM_DIFF_RATE"]),
                )
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for installments.")
    except Exception as e:
        print(e)
