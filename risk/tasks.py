from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.utils.timezone import make_aware

import pandas as pd
import io
import pyodbc
from decimal import Decimal

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal

@shared_task()
def fetch_amounts_and_debits(company):
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
        amount_debit_transactions = AmountDebitTransaction.objects.select_related().all()
        leases = Lease.objects.select_related().filter(contract__project__icontains="KORU AURA")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        amount_debit_transaction_by_code = {a.trn_id: a for a in amount_debit_transactions if a.trn_id}
        leases_dict = {l.lease_id: l for l in leases}

        previous_progress = 0
        conn = pyodbc.connect(connectionString)
        for index,obj in enumerate(leases):
            current_progress = ((index + 1)/len(leases))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")
            
            ####faiz oranını yakala
            SQL_QUERY = f"""
            SELECT *
                FROM TradeOverdueInterestRate
                WHERE
                    LeasingOperationProjectId='{obj.lease_id}'
                    AND OverdueType=1
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()

            external_data=[
                {
                    "InterestRate" : r.InterestRate,
                    "OverdueType" : r.OverdueType,
                }
                for r in records
            ]

            interest_rate = Decimal(str(external_data[0]["InterestRate"])) if len(external_data) > 0 else  Decimal("0.00")
            
            ####temerrüt hesapla
            SQL_QUERY = f"""
            SELECT
                TrnId,
                TrnIsDeleted,
                TrnJournalHeaderId,
                TrnTemplateType,
                TrnPostingType,
                TrnPostingTypeDetail,
                TrnPostingGroupId,
                TrnAccountId,
                TrnAccountCode,
                TrnOprCustomerId,
                TrnOprContractId,
                TrnOprProjectId,
                TrnOprLeasingOperationPrjId,
                TrnCurrencyCode,
                TrnAmountType,

                (CASE
                    WHEN (
                        lopStatu.RiskIncludingTypeId = 6
                        AND TrnLedgerStatu = 10
                        AND (
                            (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                            OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                        )
                        AND TrnDueDate <= '20250825'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                    THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                    ELSE TrnAmount
                END) AS TrnAmount,

                ROUND((
                    (CASE
                        WHEN (
                            lopStatu.RiskIncludingTypeId = 6
                            AND TrnLedgerStatu = 10
                            AND (
                                (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                                OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                            )
                            AND TrnDueDate <= '20250825'
                            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                        )
                        THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                        ELSE TrnAmount
                    END) * TrnExchangeRateLocal), 2
                ) AS TrnAmountLocal,

                TrnExchangeRateLocal,
                TrnExchangeRateCILocal,
                TrnAmountCapital,
                TrnAmountCapitalLocal,
                TrnAmountInterest,
                TrnVATAmount,
                TrnVATRate,
                TrnDueDate,
                TrnReturnDocumentDate,
                TrnReturnDocumentNo,
                TrnReturnDocumentDescription,

                JrnStpPstGrpName AS JrnStpPstGrpName,
                ISNULL(JrnStpPstGrpOverdueId, JrnStpPstGrpId) AS TrnPostingGroupIdOverdue,
                PART_ID,
                con.CustomerTypeId,
                AccName AS viewTrnAccountId,
                lopStatu.VatRate,
                lopStatu.RiskIncludingTypeId,
                lopStatu.OperationProjectCode,

                CAST(0 AS NUMERIC(18, 2)) AS TrnRateBSMV,
                lopStatu.AppliedTaxAdvantageAmount AS TrnRateKKDF,
                lopStatu.OVERDUE_GRACE_PERIOD,
                cp.ContractProjectCode,
                e1.JrnStpEnumDescription AS viewTrnPostingType,
                0 AS IsDeleted,

                ContractHeaderCode = CASE
                    WHEN ISNULL(con.TransferCode, '') = '' THEN con.ContractHeaderCode
                    ELSE con.TransferCode
                END,

                ContractHeaderCodeLop = CASE
                    WHEN ISNULL(lopStatu.TransferCode, '') = '' THEN lopStatu.OperationProjectCode
                    ELSE lopStatu.TransferCode
                END,

                dbo.CrmGetCustomerMailAddress(CrmCustomerWithTypesLight.OBJECT_ID, CrmCustomerWithTypesLight.CustomerTypeId) AS Email

            FROM TradeTransaction (NOLOCK)

            LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)
                ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId
            AND TrnOprCustomerId = lopStatu.CustomerId

            LEFT JOIN (
                SELECT
                    kk.OperationProjectId AS OperationProject_Id,
                    COUNT(*) AS OperationProjectId_Count
                FROM LeasingOperationProject kk (NOLOCK)
                WHERE NOT (
                    kk.RiskIncludingTypeId IN (3, 6)
                    OR (kk.RiskIncludingTypeId IN (9, 5) AND kk.OperationTypeId = 1)
                )
                GROUP BY kk.OperationProjectId
            ) xx
                ON xx.OperationProject_Id = lopStatu.OperationProjectId

            LEFT JOIN LeasingOperationProject lopX (NOLOCK)
                ON lopX.OperationProjectId = (
                    CASE
                        WHEN TrnOprRevisionLOPId <> 0 THEN TrnOprRevisionLOPId
                        ELSE TrnOprLeasingOperationPrjId
                    END
                )

            LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK)
                ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId

            LEFT JOIN TradeAccount (NOLOCK)
                ON TrnAccountId = TradeAccount.AccId

            LEFT JOIN ContractProject cp (NOLOCK)
                ON TrnOprProjectId = cp.ContractProjectId

            LEFT JOIN ContractHeader con (NOLOCK)
                ON TrnOprContractId = con.ContractHeaderId

            LEFT JOIN JournalSetupEnums e1 (NOLOCK)
                ON TrnPostingType = e1.JrnStpEnumValue
            AND e1.JrnStpEnumType = 50

            LEFT JOIN CrmCustomerWithTypesLight (NOLOCK)
                ON con.CustomerId = CrmCustomerWithTypesLight.CustomerId

            WHERE
                TrnDummy = 0
                AND (
                    TrnIsDeleted NOT IN (6,4,2,8,1)
                    OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
                )
                AND (
                    TrnLayer = 1
                    OR (
                        lopStatu.RiskIncludingTypeId = 6
                        AND TrnLayer = 3
                        AND (
                            (TrnPostingType >= 110 AND TrnPostingType <= 120)
                            OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                        )
                        AND TrnDueDate <= '20250825'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                )
                AND (
                    ISNULL(xx.OperationProjectId_Count, 0) > 0
                    OR (
                        ISNULL(xx.OperationProjectId_Count, 0) = 0
                        AND TrnPostingType <> 126
                    )
                )
                AND (
                    TrnLedgerStatu = 50
                    OR (
                        lopStatu.RiskIncludingTypeId = 6
                        AND TrnLedgerStatu = 10
                        AND TrnPostingType >= 110
                        AND TrnPostingType <= 120
                        AND TrnDueDate <= '20250825'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                )
                AND TrnAccountType = 11
                AND TrnAccountId <> 0
                AND TrnDueDate <= CONVERT(DATETIME, '2025-08-25', 102)

                -- FARK BURADA
                AND TrnOprLeasingOperationPrjId IN ({obj.lease_id})
                --AND TrnOprContractId IN ()

                AND (
                    lopStatu.LastSubStatuId IN (
                        405,416,415,402,2028,2057,2041,2058,2059,
                        408,2073,806,412,2047,503,1026,1014,2032,
                        2072,4507,2060,406,2031,2061,1009,414,1010,
                        2065,2066,2062,410,401,403,1007,1019,805,
                        1041,2029,2063,2064,400,404
                    )
                    OR TrnOprLeasingOperationPrjId = 0
                )

            ORDER BY
                TrnAccountId,
                TrnPostingGroupId,
                TrnOprContractId,
                TrnOprProjectId,
                TrnOprLeasingOperationPrjId,
                TrnCurrencyCode,
                TrnDueDate,
                TrnId;
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()

            external_data=[
                {
                    "TrnId" : r.TrnId,
                    "JrnStpPstGrpName" : r.JrnStpPstGrpName,
                    "TrnCurrencyCode" : r.TrnCurrencyCode,
                    "TrnDueDate" : r.TrnDueDate,
                    "viewTrnPostingType" : r.viewTrnPostingType,
                    "TrnAmount" : r.TrnAmount,
                    "TrnAmountLocal" : r.TrnAmountLocal,
                    "TrnAmountType" : r.TrnAmountType,
                }
                for r in records
            ]

            for index,data in enumerate(external_data):
                if str(data["TrnId"]):
                    obj = (amount_debit_transaction_by_code.get(str(data["TrnId"])))
                else:
                    obj = None

                if obj:
                    old_obj_count += 1
                    trn_id = str(data["TrnId"]) or ""
                    lease = leases_dict.get(str(data["TrnOprLeasingOperationPrjId"]))
                    process_group = str(data["JrnStpPstGrpName"]) or ""
                    due_date = make_aware(data["TrnDueDate"]) if data["TrnDueDate"] else None
                    process_type = str(data["viewTrnPostingType"]) or ""

                    debit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "1" else Decimal("0.00")
                    credit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "0" else Decimal("0.00")
                    real_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "1" else Decimal("0.00")
                    for_default_amount = safe_decimal(data["VatRate"])
                    adat_amount = safe_decimal(data["VatRate"])
                    default_amount = safe_decimal(data["VatRate"])
                    interest_rate = safe_decimal(data["VatRate"])
                    overdue_interest_rate = safe_decimal(data["VatRate"])

                    day = int(data["TrnId"]) or 0

                    # obj.contract_id = str(data["ContractHeaderId"]) or ""
                    # obj.code = str(data["ContractHeaderCode"]) or ""
                    # obj.partner = partners_dict.get(str(data["CustomerId"]))
                    # obj.quotation_obj = quotations_dict.get(str(data["QuotationHeaderId"]))
                    # obj.committe = str(data["CommitteeName"]) or ""
                    # obj.credit_type = str(data["CreditTypeName"]) or ""
                    # obj.customer_representative = str(data["CustomerRepresentative"]) or ""
                    # obj.supplier = data["Vendor"] or ""
                    # obj.project = data["Project"] or ""
                    # obj.status = statuses_dict.get(normalize(data["SubStatuteName"]))
                    # obj.lop_open_date = make_aware(data["LopOpenDate"]) if data["LopOpenDate"] else None
                    # obj.currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"])
                    # obj.save()
                else:
                    pass
        
    except Exception as e:
        print(e)
