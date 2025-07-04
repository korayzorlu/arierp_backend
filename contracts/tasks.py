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

@shared_task()
def fix_contracts():
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
        FROM ContractHeader
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "id" : r.ContractHeaderId,
                "code" : r.ContractHeaderCode,
            }
            for r in records
        ]
        print(len(external_data))
        for data in external_data:
            obj = Contract.objects.select_related().filter(code = str(data["code"])).first()
            if obj:
                obj.contract_id = str(int(data["id"]))
                obj.save()
    except Exception as e:
        print(e)