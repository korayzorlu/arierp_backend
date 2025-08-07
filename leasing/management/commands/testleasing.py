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

        # installments = Installment.objects.select_related("lease").filter(lease__lease_id="73745")

        # installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency is not None}
        
        # obj = (installment_by_code.get(("73745",int(0))))

        # print(f"{obj.sequency} - {obj.payment_date} - {obj.amount}")

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

        conn = pyodbc.connect(connectionString)
        cursor = conn.cursor()

        try:
            SQL_QUERY = f'''
                SELECT 
                    TrnIsDeleted,
                    TrnPostingType,
                    TrnPostingGroupId,
                    TrnAccountId,
                    TrnOprCustomerId,
                    TrnOprContractId,
                    TrnOprProjectId,
                    TrnOprLeasingOperationPrjId,
                    TrnAmountType,

                    (
                        CASE 
                            WHEN (
                                lopStatu.RiskIncludingTypeId = 6 
                                AND TrnLedgerStatu = 10 
                                AND (
                                    (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                                    OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                                )
                                AND TrnDueDate <= '20250722'
                                AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                            )
                            THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                            ELSE TrnAmount
                        END
                    ) AS TrnAmount,

                    ROUND(
                        (
                            (
                                CASE 
                                    WHEN (
                                        lopStatu.RiskIncludingTypeId = 6 
                                        AND TrnLedgerStatu = 10 
                                        AND (
                                            (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                                            OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                                        )
                                        AND TrnDueDate <= '20250722'
                                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                                    )
                                    THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                                    ELSE TrnAmount
                                END
                            ) * TrnExchangeRateLocal
                        ), 
                        2
                    ) AS TrnAmountLocal,

                    TrnExchangeRateLocal,
                    TrnAmountCapital,
                    TrnAmountInterest,
                    TrnVATAmount,
                    TrnDueDate,
                    TrnReturnDocumentNo,
                    JrnStpPstGrpName AS JrnStpPstGrpName,
                    ISNULL(JrnStpPstGrpOverdueId, JrnStpPstGrpId) AS TrnPostingGroupIdOverdue,
                    PART_ID,
                    con.CustomerTypeId,
                    lopStatu.VatRate,
                    lopStatu.RiskIncludingTypeId,
                    lopStatu.OperationProjectCode,
                    CAST(0 AS NUMERIC(18,2)) AS TrnRateBSMV,
                    lopStatu.AppliedTaxAdvantageAmount AS TrnRateKKDF,
                    lopStatu.OVERDUE_GRACE_PERIOD,
                    cp.ContractProjectCode,
                    e1.JrnStpEnumDescription AS viewTrnPostingType,
                    0 AS IsDeleted,

                    ContractHeaderCode = CASE 
                        WHEN ISNULL(con.TransferCode, '') = '' 
                        THEN con.ContractHeaderCode  
                        ELSE con.TransferCode 
                    END,

                    ContractHeaderCodeLop = CASE 
                        WHEN ISNULL(lopStatu.TransferCode, '') = '' 
                        THEN lopStatu.OperationProjectCode  
                        ELSE lopStatu.TransferCode 
                    END,

                    dbo.CrmGetCustomerMailAddress(
                        CrmCustomerWithTypesLight.OBJECT_ID,
                        CrmCustomerWithTypesLight.CustomerTypeId
                    ) AS Email

                FROM 
                    TradeTransaction (NOLOCK)

                LEFT JOIN 
                    LOPRevisionJoinMainList lopStatu (NOLOCK)
                    ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId 
                    AND TrnOprCustomerId = lopStatu.CustomerId

                LEFT JOIN 
                    (
                        SELECT 
                            kk.OperationProjectId AS OperationProject_Id,
                            COUNT(*) AS OperationProjectId_Count
                        FROM 
                            LeasingOperationProject kk (NOLOCK)
                        WHERE 
                            NOT (
                                kk.RiskIncludingTypeId IN (3, 6) 
                                OR (kk.RiskIncludingTypeId IN (9, 5) AND kk.OperationTypeId = 1)
                            )
                        GROUP BY 
                            kk.OperationProjectId
                    ) xx 
                    ON xx.OperationProject_Id = lopStatu.OperationProjectId

                LEFT JOIN 
                    LeasingOperationProject lopX (NOLOCK) 
                    ON lopX.OperationProjectId = (
                        CASE 
                            WHEN TrnOprRevisionLOPId <> 0 
                            THEN TrnOprRevisionLOPId 
                            ELSE TrnOprLeasingOperationPrjId 
                        END
                    )

                LEFT JOIN 
                    JournalSetupPostingTypeGroups (NOLOCK) 
                    ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId

                LEFT JOIN 
                    TradeAccount (NOLOCK) 
                    ON TrnAccountId = TradeAccount.AccId

                LEFT JOIN 
                    ContractProject cp (NOLOCK) 
                    ON TrnOprProjectId = cp.ContractProjectId

                LEFT JOIN 
                    ContractHeader con (NOLOCK) 
                    ON TrnOprContractId = con.ContractHeaderId

                LEFT JOIN 
                    JournalSetupEnums e1 (NOLOCK) 
                    ON TrnPostingType = e1.JrnStpEnumValue 
                    AND e1.JrnStpEnumType = 50

                LEFT JOIN 
                    CrmCustomerWithTypesLight (NOLOCK) 
                    ON con.CustomerId = CrmCustomerWithTypesLight.CustomerId

                WHERE 
                    TrnOprContractId = 41727 AND
                    TrnOprLeasingOperationPrjId = 75289
                    --AND JrnStpPstGrpName = 'Kira'

                ORDER BY 
                    TrnDueDate

            '''
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            external_data=[
                {   
                    "type" : r.TrnAmountType,
                    "amount" : r.TrnAmount,
                    "due_date" : r.TrnDueDate,
                    "group" : r.JrnStpPstGrpName,
                    "posting_type" : r.viewTrnPostingType,
                    "document_no" : r.TrnReturnDocumentNo,
                    "contract_id" : r.TrnOprContractId,
                }
                for r in records
            ]

            type_0_total = sum(Decimal(str(item["amount"])) for item in external_data if item["type"] == 0)
            type_1_total = sum(Decimal(str(item["amount"])) for item in external_data if item["type"] == 1)
            type_0_total = type_0_total - Decimal("9026")

            result = f"borç: {type_1_total} | tahsilat: {type_0_total} | bakiye: {type_1_total - type_0_total}"

            print(result)


        except Exception as e:
            print(e)
        
        print("done!")