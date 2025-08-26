from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.utils.timezone import make_aware

import pandas as pd
import io
import pyodbc

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal

@shared_task()
def fetch_contracts(company):
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
        contracts = Contract.objects.select_related().filter(project__icontains="KORU AURA")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        contract_by_code = {c.contract_id: c for c in contracts if c.contract_id}

        previous_progress = 0
        conn = pyodbc.connect(connectionString)
        for index,contract in enumerate(contracts):
            current_progress = ((index + 1)/len(contracts))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            SQL_QUERY = """
            SELECT ContractHeaderId,
                ContractHeaderCode,
                CustomerId,
                QuotationHeaderId,
                CommitteeName,
                CreditTypeName,
                CustomerRepresentative,
                Vendor,
                Project,
                SubStatuteName,
                LopOpenDate,
                CurrencyCode
            FROM ContractHeaderLightList
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()

            external_data=[
                {
                    "ContractHeaderId" : r.ContractHeaderId,
                    "ContractHeaderCode" : r.ContractHeaderCode,
                    "CustomerId" : r.CustomerId,
                    "QuotationHeaderId" : r.QuotationHeaderId,
                    "CommitteeName" : r.CommitteeName,
                    "CreditTypeName" : r.CreditTypeName,
                    "CustomerRepresentative" : r.CustomerRepresentative,
                    "Vendor" : r.Vendor,
                    "Project" : r.Project,
                    "SubStatuteName" : r.SubStatuteName,
                    "LopOpenDate" : r.LopOpenDate,
                    "CurrencyCode" : r.CurrencyCode,
                }
                for r in records
            ]

        
    except Exception as e:
        print(e)
