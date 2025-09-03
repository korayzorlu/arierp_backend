from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from leasing.models import *
from contracts.tasks import fetch_warning_notices

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
        
        fetch_warning_notices.delay(company)

        # SERVER = "192.168.82.31,1433"
        # DATABASE = "ARI_LEASING"
        # USERNAME = "lflex"
        # PASSWORD = "S!gma2014"

        # connectionString = f'''
        #     DRIVER={{ODBC Driver 18 for SQL Server}};
        #     SERVER={SERVER};
        #     DATABASE={DATABASE};
        #     UID={USERNAME};
        #     PWD={PASSWORD};
        #     Provider=SQLNCLI11;
        #     Integrated Security=SSPI;
        #     Persist Security Info=False;
        #     Initial Catalog=MASTER;
        #     TrustServerCertificate=yes;
        # '''

        # try:
        #     conn = pyodbc.connect(connectionString)
            
        #     SQL_QUERY = """
        #         SELECT RiskDocumentId,
        #             RiskHeaderId,
        #             CustomerId,
        #             ContractHeaderId,
        #             OrgContractHeaderId,
        #             Debit,
        #             ProcessStartDate,
        #             DailyWagesDate,
        #             ServiceDate,
        #             OfficialCancellationDate,
        #             Paid,
        #             Diff,
        #             State,
        #             ApprovalState,
        #             ResultId,
        #             PROCESS_SITUATION_ID
        #             FROM RiskDocumentWarningFollowListBaseLPDDOR
        #             WHERE
        #                 (PROCESS_SITUATION_ID is null or ResultId in (0,1,2)) 
        #                 AND 1=1
        #                 --AND CustomerId=29308
        #                 AND ResultId in (0,1)
        #                 AND ContractHeaderId='53233/1'
        #     """

        #     cursor = conn.cursor()
        #     cursor.execute(SQL_QUERY)
            
        #     records = cursor.fetchall()

        #     external_data=[
        #         {
        #             "RiskDocumentId" : r.RiskDocumentId,
        #             "RiskHeaderId" : r.RiskHeaderId,
        #             "CustomerId" : r.CustomerId,
        #             "OrgContractHeaderId" : r.OrgContractHeaderId,
        #             "Debit" : r.Debit,
        #             "ProcessStartDate" : r.ProcessStartDate,
        #             "DailyWagesDate" : r.DailyWagesDate,
        #             "ServiceDate" : r.ServiceDate,
        #             "OfficialCancellationDate" : r.OfficialCancellationDate,
        #             "Paid" : r.Paid,
        #             "Diff" : r.Diff,
        #             "State" : r.State,
        #             "ApprovalState" : r.ApprovalState,
        #         }
        #         for r in records
        #     ]

        #     print(external_data)
           
        # except Exception as e:
        #     print(e)  
        
        print("done!")