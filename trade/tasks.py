from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io
import pyodbc

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from .utils.trade_transaction_utils import fetch_trade_transactions_from_leaseflex

@shared_task()
def transfer_trade_accounts(company):
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
                "partner" : r.AccCrmId,
                "crm_type" : r.AccCrmType,
                "account_id" : r.AccId,
                "name" : r.AccName,
            }
            for r in records
        ]

        for data in external_data:
            if TradeAccount.objects.select_related().filter(account_id = str(int(data["account_id"]))).exists():
                obj = TradeAccount.objects.select_related().filter(account_id = str(int(data["account_id"]))).first()
                obj.crm_type = "Bireysel Müşteri" if str(data["crm_type"]) == "B" else "Kurumsal Müşteri"
                obj.save()
                continue
            obj = TradeAccount.objects.create(
                company = Company.objects.select_related().filter(id = int(company)).first(),
                partner = Partner.objects.select_related().filter(crm_code = str(data["partner"])).first() if not pd.isna(data["partner"]) else None,
                account_id = str(int(data["account_id"])) if not pd.isna(data["account_id"]) else "",
                crm_type = str(data["crm_type"]) if not pd.isna(data["crm_type"]) else "",
                crm_id = str(data["partner"]) if not pd.isna(data["partner"]) else "",
                name = data["name"] if not pd.isna(data["name"]) else "",
            )
            obj.save()
    except Exception as e:
        print(e)

@shared_task()
def fetch_trade_transactions(company,BATCH_SIZE=1000,contract_code=None):
    fetch_trade_transactions_from_leaseflex(company,BATCH_SIZE=BATCH_SIZE,contract_code=contract_code)