from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from ledger.models import *

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

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')

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
        
        print("done!")