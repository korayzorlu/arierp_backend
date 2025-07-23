from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os
from bs4 import BeautifulSoup
import pyodbc
from decimal import Decimal

from leasing.models import Lease,Installment

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

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

        conn = pyodbc.connect(connectionString)
        cursor = conn.cursor()

        try:
            SQL_QUERY = f'''
                SELECT *
                    FROM [ARI_LEASING].[dbo].[TradeTransactionLightList]
                    WHERE TrnOprLeasingOperationPrjId=55734 AND TrnDueDate <= CONVERT(DATETIME, '2025-7-22', 102) AND TrnAccountType = 11 AND TrnAccountId <> 0 AND TrnIsDeleted != 1
                    ORDER BY TrnReturnCounter, TrnDueDate

            '''
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            external_data=[
                {   
                    "type" : r.TrnAmountType,
                    #"viewTrnAccountId" : r.viewTrnAccountId,
                    "viewTrnPostingType" : r.viewTrnPostingType,
                    "viewTrnOprLeasingOprPrjId" : r.viewTrnOprLeasingOprPrjId,
                    "TrnReturnCounter" : r.TrnReturnCounter,
                    "TrnAmount" : r.TrnAmount,
                    "TrnDueDate" : r.TrnDueDate,
                }
                for r in records
            ]
            for data in external_data:
                print(data)
            type_0_total = sum(Decimal(str(item["TrnAmount"])) for item in external_data if item["viewTrnPostingType"] == "Tahsilatlar")
            type_1_total = sum(Decimal(str(item["TrnAmount"])) for item in external_data if item["viewTrnPostingType"] == "Kira - Normal")
            #type_0_total = type_0_total - Decimal("9026")

            result = f"borç: {type_1_total} | tahsilat: {type_0_total} | bakiye: {type_1_total - type_0_total}"

            print(result)


        except Exception as e:
            print(e)
        
        print("done!")