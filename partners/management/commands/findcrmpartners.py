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
            FROM CrmCustomerWithTypes
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()

            external_data=[
                {
                    "customerId" : r.CustomerId,
                    "customerCode" : r.CustomerCode,
                    "customerName" : r.CustomerName
                }
                for r in records
            ]

            for data in external_data:
                if data["customerCode"] and data["customerCode"] != "ARI":
                    obj = Partner.objects.select_related().filter(customer_code = str(int(data["customerCode"]))).first()
                    if obj:
                        obj.crm_code = data["customerId"]
                        obj.save()
        except Exception as e:
            print(e)
        
        print("done!")