from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io
import pyodbc

from .models import *
from users.models import User
from contracts.models import *

@shared_task()
def transfer_ledger_accounts(company):
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
        FROM LedgerAccount
        WHERE
            AccountType='1'
            AND (
                AccountCode LIKE '150%' OR
                AccountCode LIKE '151%' OR
                AccountCode LIKE '176%' OR
                AccountCode LIKE '278.99%' OR
                AccountCode LIKE '279.99%' OR
                AccountCode LIKE '226%' OR
                AccountCode LIKE '227%' OR
                AccountCode LIKE '392.99%' OR
                AccountCode LIKE '393.99%' OR
                AccountCode LIKE '924%' OR
                AccountCode LIKE '926%' OR
                AccountCode LIKE '978.58%' OR
                AccountCode LIKE '980.58%' OR
                AccountCode LIKE '170%' OR
                AccountCode LIKE '171%' OR
                AccountCode LIKE '154%' OR
                AccountCode LIKE '155%' OR
                AccountCode LIKE '177%'
            )
        ORDER BY AccountCode
        OFFSET 389000 ROWS
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()
        external_data=[
            {   
                "account_id" : r.AccountId,
                "partner" : r.Dimension3,
                "contract" : r.Dimension8,
                "code" : r.AccountCode,
                "name" : r.AccountName,
                "currency" : r.AccountCurrencyCode
            }
            for r in records
        ]
        for data in external_data:
            if LedgerAccount.objects.select_related().filter(account_id = str(int(data["account_id"]))).exists():
                continue
            if not pd.isna(data["currency"]) and data["currency"] == "TL":
                data["currency"] =  "TRY"
            obj = LedgerAccount.objects.create(
                company = Company.objects.select_related().filter(id = int(company)).first(),
                partner = Partner.objects.select_related().filter(crm_code = str(data["partner"])).first() if not pd.isna(data["partner"]) else None,
                account_id = str(int(data["account_id"])) if not pd.isna(data["account_id"]) else "",
                code = data["code"] if not pd.isna(data["code"]) else "",
                name = data["name"] if not pd.isna(data["name"]) else "",
                currency = Currency.objects.select_related().filter(code = data["currency"]).first() if not pd.isna(data["currency"]) else None,
            )
            obj.save()
    except Exception as e:
        print(e)