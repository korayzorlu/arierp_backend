from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os
import pyodbc
import json


class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        
        SERVER = "192.168.81.5,1433"
        DATABASE = "ARI_LEASING"
        USERNAME = "ARILEASING/koray.zorlu"
        PASSWORD = "Kozo5313-*"

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
            SELECT DISTINCT   0 AS Trn_Temp_RevenueCheckColumn,TrnId,TrnFromToType AS TrnFromToType_HIDDEN,TrnFromLedgerAccountId AS TrnFromLedgerAccountId_HIDDEN,TrnFromTradeAccountCode AS TrnFromTradeAccountCode_HIDDEN,TrnFromId=CASE 
            TrnFromToType WHEN 10 THEN tatFrom.AccTypUniqueId WHEN 20 THEN LedgerAccount.AccountCode ELSE '' END ,AccountCode AS TrnFromLedgerAccountId_AC,AccountName AS TrnFromLedgerAccountId_AN,tatFrom.AccTypUniqueId AS 
            TrnFromTradeAccountCode,e1.JrnStpEnumDescription AS viewTrnFromToType,e2.JrnStpEnumDescription AS viewTrnPostingType,TrnPostingType,'' Status,1 StatusId,JrnStpPstGrpName AS JrnStpPstGrpName,ch.ContractHeaderCode as 
            TrnOprContractId,TrnAccountCode,ta.AccName,tat.AccTypUniqueId AS OPR_AccTypUniqueId,tat.AccName AS OPR_AccName,TrnDate,TrnDueDate,TrnAmountTypeDebit=CASE TrnAmountType WHEN 1 THEN TrnAmount ELSE 0 END 
            ,TrnAmountTypeCredit=CASE TrnAmountType WHEN 0 THEN TrnAmount ELSE 0 END ,TrnCurrencyCode,TrnAmountTypeLocalDebit=CASE TrnAmountType WHEN 1 THEN TrnAmountLocal ELSE 0 END ,TrnAmountTypeLocalCredit=CASE TrnAmountType WHEN 0 
            THEN TrnAmountLocal ELSE 0 END ,TrnExchangeRateLocal,TrnLegalExchangeRateLocal_TEMP=CASE  WHEN TrnLegalExchangeRateLocal=TrnExchangeRateLocal THEN ''  ELSE 'X' END ,TrnDescription,TrnIsPlanned+TrnReturnValueId AS 
            TrnIsPlanned,TrnIsPlanned_INFO=CASE TrnSourceType WHEN 3 THEN 'Banka Otomasyonu' WHEN 31 THEN 'ATS Banka Oto.' WHEN 32 THEN 'BTS Banka Oto.' WHEN 33 THEN 'ZİNCİRLİKUYU Banka Oto.' WHEN 2 THEN 'Aktarım Datası' WHEN 80 THEN 'Otomatik Tahsilat' WHEN 60 THEN 'EFT' WHEN 90 THEN 'Satıcı Avansı Tahsilatı' ELSE CASE TrnIsPlanned WHEN 1 THEN 'Planlanmış' ELSE (CASE TrnReturnValueId WHEN 0 THEN 'Elle Girilmiş' ELSE 'Modülden Gelmiş' END ) END  END ,userx.NameSurname AS CreatedUserId,TrnReturnDocumentNo,TrnCommittedRefId  FROM TradeTransaction (NOLOCK)   LEFT JOIN FoundationUserList userx (nolock) ON (CASE TrnCommittedRefId WHEN 0 THEN TrnUserId ELSE (SELECT subTT.TrnUserId  FROM TradeTransaction subTT (NOLOCK)  WHERE subTT.TrnId=TradeTransaction.TrnCommittedRefId ) END )=userx.UserId LEFT JOIN JournalSetupEnums e1 (nolock) ON TrnFromToType=e1.JrnStpEnumValue AND e1.JrnStpEnumType=80 LEFT JOIN JournalSetupEnums e2 (nolock) ON TrnPostingType=e2.JrnStpEnumValue AND e2.JrnStpEnumType=50 LEFT JOIN LedgerAccount (nolock) ON TrnFromLedgerAccountId=LedgerAccount.AccountId LEFT JOIN ContractHeader ch (nolock) ON TrnOprContractId=ch.ContractHeaderId LEFT JOIN TradeAccount ta (nolock) ON TrnAccountId=ta.AccId LEFT JOIN JournalSetupPostingTypeGroups (nolock) ON TrnPostingGroupId=JournalSetupPostingTypeGroups.JrnStpPstGrpId LEFT JOIN TradeAccountAndTypeComboList tat (nolock) ON TrnOprCustomerId=tat.AccCrmId AND tat.AccTypType=11 LEFT JOIN TradeAccountTypes tatFrom (nolock) ON TrnFromTradeAccountCode=tatFrom.AccTypUniqueId AND tatFrom.AccTypType=31 AND TrnFromToType=10  WHERE TrnDummy=0 AND (TrnIsDeleted NOT IN (6,4,2,8,1) OR (TrnIsDeleted=6 AND TrnAmount<>0)) AND TrnAccountType IN (21,11,1) AND TrnDate>=CONVERT(DATETIME, '2025-6-1',102) AND TrnDate<=CONVERT(DATETIME, '2025-6-26',102) AND TrnLayer=1 AND TrnLedgerStatu=50 AND ISNULL(TrnFromToType,0)<>0 AND TrnTemplateType<>0 AND TrnAmountType=0 AND TrnPostingType IN (221,211,101,102,103,931,482)  ORDER BY TrnDueDate,AccountName 
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            # for r in records:
                
            #     row_to_list = [elem for elem in r]
            external_data=[]
            id = 1
            for r in records:
                row_to_list = [elem for elem in r]
                
                external_data.append({
                    "id" : id,
                    "TrnDescription" : r.TrnDescription,
                })
                
                id = id + 1
            for data in external_data:
                print(data)
        except Exception as e:
            print(e)



