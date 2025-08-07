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
            SELECT 0 AS TrnConsolideId,'' AS 
            TrnConsolideInfo,TrnId,TrnSourceType,TrnIsDeleted,PART_ID,CrmCustomerWithTypesLightTradeRisk.CustomerId AS 
            CustomerId,CrmCustomerWithTypesLightTradeRisk.CustomerName AS 
            viewTrnAccountId,RATING,TrnAccountId,TrnDescription,TrnOffsetInfo,TrnCurrencyCode,TrnContractBlock=CASE  WHEN 
            ISNULL(lopStatu.OperationProjectId,0)<>0  THEN lopStatu.OperationProjectCode  WHEN ISNULL(cp.ContractProjectId,0)<>0 THEN 
            cp.ContractProjectCode  ELSE CAST(TrnOprContractId AS VARCHAR(100)) END ,substatu.DefinitionName,(case when 
            Isnull(lopStatu.HasGuarantor,0)=1 then 'Evet' else 'Hayır' end) as HasGuarantor,TrnPostingGroupId,JrnStpPstGrpName AS 
            JrnStpPstGrpName,TrnTemplateType,TrnPostingType,TrnPostingTypeDetail,e1.JrnStpEnumDescription AS 
            viewTrnPostingType,TrnReturnDocumentNo,TrnDueDate,TrnDate AS LedgeredDate,TrnReturnDocumentDate AS 
            TrnReturnDocumentDate,TrnExchangeRateLocal,TrnJournalHeaderId,TrnOprContractId,TrnOprProjectId,ISNULL(TrnOprLeasingOperationPrjId,0) 
            AS TrnOprLeasingOperationPrjId,TrnCreateDate,TrnAmountType,TrnAmount,TrnAmountLocal,0 AS VoucherCode , rprData.PROJECT_NAME, 
            rprData.BLOCK_NO, rprData.FREE_PART_NO FROM TradeTransaction (NOLOCK)  LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)  ON 
            TrnOprLeasingOperationPrjId=lopStatu.SourceLopId AND TrnOprCustomerId=lopStatu.CustomerId  LEFT JOIN TradeAccount (nolock) ON 
            TrnAccountId=TradeAccount.AccId LEFT JOIN CrmCustomerWithTypesLightTradeRisk (nolock) ON 
            AccCrmId=CrmCustomerWithTypesLightTradeRisk.CustomerId LEFT JOIN JournalSetupPostingTypeGroups (nolock) ON TrnPostingGroupId=JournalSetupPostingTypeGroups.JrnStpPstGrpId LEFT JOIN JournalSetupEnums e1 (nolock) ON TrnPostingType=e1.JrnStpEnumValue AND e1.JrnStpEnumType=50 LEFT JOIN FoundationStatuteMenu substatu (nolock) ON lopStatu.LastSubStatuId=substatu.DefinitionId LEFT JOIN ContractProject cp (nolock) ON TrnOprProjectId=cp.ContractProjectId   LEFT JOIN QuotationProject qp (nolock) ON cp.QuotationProjectId=qp.ProjectId LEFT JOIN RPR_PROJECT_VGKA_REPORT_DATA rprData (nolock) ON TrnOprLeasingOperationPrjId=rprData.OPERATION_PROJECT_ID  WHERE TrnDummy=0 AND (CASE WHEN TrnIsDeleted=4 AND  lopStatu.RiskIncludingTypeId=7 AND  (SELECT lll.RiskIncludingTypeId FROM LeasingOperationProject lll (NOLOCK) WHERE lll.OperationProjectId=lopStatu.OperationProjectId)=6 THEN 3 WHEN TrnIsDeleted=4 AND  lopStatu.RiskIncludingTypeId=6 AND  (SELECT TOP 1 lll.RiskIncludingTypeId FROM LOPRevisionJoinListOutPlan lll (NOLOCK) WHERE (lll.OperationProjectId=TrnOprRevisionLOPId AND TrnOprRevisionLOPId<>0) OR (lll.OperationProjectId=TrnOprLeasingOperationPrjId AND TrnOprRevisionLOPId=0) )=7 THEN 3 ELSE TrnIsDeleted END NOT IN (6,4,2,8,1) OR (TrnIsDeleted=6 AND TrnAmount<>0)) AND (TrnAmount<>0 OR TrnAmountLocal<>0 OR TrnAmountCompany<>0) AND TrnLayer=1 AND TrnLedgerStatu=50 AND NOT (TrnIsDeleted=2 AND TrnPostingType>120 AND TrnPostingType<110) AND TrnPostingType<>461 AND (lopStatu.LastSubStatuId IN (405,416,415,402,2028,2057,2041,2058,2059,408,2073,806,412,2047,503,1026,1014,2032,2072,4507,2060,406,2031,2061,1009,414,1010,2065,2066,2062,410,401,403,1007,1019,805,1041,2029,2063,2064,400,404) OR ISNULL(TrnOprLeasingOperationPrjId,0)=0) AND TrnPostingGroupId IN (1,4,6,7,9,13,16,17,19,20,21,23,27,28,29) AND TrnAccountType=11  ORDER BY TrnAccountId,TrnCurrencyCode,TrnOprContractId,TrnOprProjectId,TrnDueDate,TrnId 
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            external_data=[
                {   
                    "cutomer_id" : r.CustomerId,
                    "view_account" : r.viewTrnAccountId,
                    "description" : r.TrnDescription,
                    "currency" : r.TrnCurrencyCode,
                    "lease" : r.TrnContractBlock,
                    "contract" : r.TrnOprContractId,
                    "definition" : r.DefinitionName,
                    "group" : r.JrnStpPstGrpName,
                    "view_position" : r.viewTrnPostingType,
                    "due_date" : r.TrnDueDate,
                    "ledgered_date" : r.LedgeredDate,
                    "document_date" : r.TrnReturnDocumentDate,
                    "exchange_rate" : r.TrnExchangeRateLocal,
                    "amount" : r.TrnAmount,
                    "local_amount" : r.TrnAmountLocal,
                    "project" : r.PROJECT_NAME
                }
                for r in records
            ]

        except Exception as e:
            print(e)

        data = {
            "Müşteri CRM": [],
            "Müşteri": [],
            "Açıklama": [],
            "Kira Planı": [],
            "Sözleşme": [],
            "Tanım": [],
            "İşlem Grubu": [],
            "İşlem Tipi": [],
            "Bakiye": [],
            "Bakiye(Yerel)": [],
            "Para Birimi": [],
            "Kur(Yerel)": [],
        }

        for obj in external_data:
            data["Müşteri CRM"].append(obj["cutomer_id"])
            data["Müşteri"].append(obj["view_account"])
            data["Açıklama"].append(obj["description"])
            data["Kira Planı"].append(obj["lease"])
            data["Sözleşme"].append(obj["contract"])
            data["Tanım"].append(obj["definition"])
            data["İşlem Grubu"].append(obj["group"])
            data["İşlem Tipi"].append(obj["view_position"])
            data["Bakiye"].append(obj["amount"])
            data["Bakiye(Yerel)"].append(obj["local_amount"])
            data["Para Birimi"].append(obj["currency"])
            data["Kur(Yerel)"].append(obj["amount"])
        
        df = pd.DataFrame(data)

        excel_dosyasi_adi = "hesaplar.xlsx"
        with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='cari_islemler_hareket_raporu', index=False)
        
        print("done!")