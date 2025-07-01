from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *

import pandas as pd
import json
import os
import pyodbc

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
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            external_data=[
                {   
                    "partner" : r.Dimension3,
                    "contract" : r.Dimension8,
                    "code" : r.AccountCode,
                    "name" : r.AccountName,
                    "currency" : r.AccountCurrencyCode
                }
                for r in records
            ]

        except Exception as e:
            print(e)

        data = {
            "Sözleşme Kodu": [],
            "Hesap Kodu": [],
            "Hesap İsmi": [],
            "Para Birimi": [],
        }

        for obj in external_data:
            data["Sözleşme Kodu"].append(obj["contract"])
            data["Hesap Kodu"].append(obj["code"])
            data["Hesap İsmi"].append(obj["name"])
            data["Para Birimi"].append(obj["currency"])
        
        df = pd.DataFrame(data)

        excel_dosyasi_adi = "hesaplar.xlsx"
        with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Hesaplar', index=False)
        
        print("done!")