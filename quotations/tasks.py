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
from .utils.quick_quotation_utils import fetch_quick_quotations_from_leaseflex
from .utils.quotation_utils import fetch_quotations_from_leaseflex

@shared_task()
def fetch_quick_quotation(company):
    fetch_quick_quotations_from_leaseflex(company)

@shared_task()
def fetch_quotation(company):
    fetch_quotations_from_leaseflex(company)

@shared_task()
def fetch_quick_quotation_projects(company):
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
        SELECT RPR_QUO_ID,
            QUO_HEADER_ID,
            PROJECT_ID
        FROM RPR_QUO_ITEM
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "RPR_QUO_ID" : r.RPR_QUO_ID,
                "QUO_HEADER_ID" : r.QUO_HEADER_ID,
                "PROJECT_ID" : r.PROJECT_ID,
            }
            for r in records
        ]

        quick_quotations = QuickQuotation.objects.select_related("project_obj","company").all()
        projects = Project.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        quick_quotation_by_code = {q.code: q for q in quick_quotations if q.code}
        projects_dict = {p.project_id: p for p in projects}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
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
                old_obj_count += 1
                obj.project_obj = projects_dict.get(str(data["PROJECT_ID"]))
                obj.save()
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")
    except Exception as e:
        print(e)