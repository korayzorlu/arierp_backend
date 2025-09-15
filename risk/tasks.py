from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.utils.timezone import make_aware,now

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime
import traceback

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from risk.utils.sql_utils import fetch_amounts_and_debits_sql,fetch_amounts_and_debits_sql_bulk

def to_date(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.date()
    return dt  # zaten date

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
        # Tüm objeleri RAM'e almadan toplu silme işlemi
        AmountDebitTransaction.objects.all().delete()
        print("All AmountDebitTransaction objects deleted.")
        amount_debit_transactions = AmountDebitTransaction.objects.select_related("lease").filter().order_by('pk')
        leases = Lease.objects.select_related().filter(contract__project__icontains="KIZILBÜK")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        amount_debit_transaction_by_code = {a.trn_id: a for a in amount_debit_transactions if a.trn_id}
        adt_by_lease_and_process = {(a.lease.lease_id, a.process_group_id, a.pk): a for a in amount_debit_transactions if a.lease.lease_id and a.process_group_id and a.pk}
        leases_dict = {l.lease_id: l for l in leases}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
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
            # records = fetch_amounts_and_debits_sql(cursor,obj)

            today = datetime.now().date().strftime("%Y%m%d")
            formatted_today = datetime.now().date()
            formatted_today = f"{formatted_today.year}-{formatted_today.month}-{formatted_today.day}"
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
                            AND TrnDueDate <= '{today}'
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
                                AND TrnDueDate <= '{today}'
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
                            AND TrnDueDate <= '{today}'
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
                            AND TrnDueDate <= '{today}'
                            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                        )
                    )
                    AND TrnAccountType = 11
                    AND TrnAccountId <> 0
                    AND TrnDueDate <= CONVERT(DATETIME, '{formatted_today}', 102)

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
                    "TrnOprLeasingOperationPrjId" : r.TrnOprLeasingOperationPrjId,
                    "TrnPostingGroupId" : r.TrnPostingGroupId,
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

            new_objs = []
            for index,data in enumerate(external_data):
                if str(data["TrnId"]):
                    obj = (amount_debit_transaction_by_code.get(str(data["TrnId"])))
                else:
                    obj = None

                if obj:
                    pass
                    # old_obj_count += 1
                    # obj.trn_id = str(data["TrnId"]) or ""
                    # obj.lease = leases_dict.get(str(data["TrnOprLeasingOperationPrjId"]))
                    # obj.process_group_id = str(data["TrnPostingGroupId"]) or ""
                    # obj.process_group = str(data["JrnStpPstGrpName"]) or ""
                    # obj.due_date = make_aware(data["TrnDueDate"]) if data["TrnDueDate"] else None
                    # obj.process_type = str(data["viewTrnPostingType"]) or ""

                    # obj.debit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "1" else Decimal("0.00")
                    # obj.credit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "0" else Decimal("0.00")

                    # obj.interest_rate = safe_decimal(interest_rate)

                    # #real amount
                    # prev_obj = (adt_by_lease_and_process.get((obj.lease.lease_id,obj.process_group_id,obj.pk-1)))
                    # if prev_obj:
                    #     obj.real_amount = (obj.debit_amount - obj.credit_amount) + prev_obj.real_amount
                    # else:
                    #     obj.real_amount = obj.debit_amount - obj.credit_amount
                    # obj.for_default_amount = obj.real_amount

                    # #day
                    # next_obj = (adt_by_lease_and_process.get((obj.lease.lease_id,obj.process_group_id,obj.pk+1)))
                    # if next_obj and obj.real_amount > 0.4:
                    #     diff_date = to_date(next_obj.due_date) - to_date(obj.due_date)
                    #     obj.day = diff_date.days
                    # elif not next_obj and obj.real_amount > 0.4:
                    #     diff_date = datetime.today().date() - obj.due_date.date()
                    #     obj.day = diff_date.days
                    # else:
                    #     obj.day = 0

                    # obj.adat_amount = obj.real_amount * obj.day
                    # obj.default_amount = (obj.real_amount * (interest_rate/100) * obj.day) / Decimal("360")
                    # obj.overdue_interest_rate = obj.default_amount + (obj.default_amount * Decimal("0.01"))
                    # obj.save()
                else:
                    new_obj_count += 1
                    obj = AmountDebitTransaction.objects.select_related("lease").create(
                        company = company_obj,
                        trn_id = str(data["TrnId"]) or "",
                        lease = leases_dict.get(str(data["TrnOprLeasingOperationPrjId"])),
                        process_group_id = str(data["TrnPostingGroupId"]) or "",
                        process_group = str(data["JrnStpPstGrpName"]) or "",
                        due_date = make_aware(data["TrnDueDate"]) if data["TrnDueDate"] else None,
                        process_type = str(data["viewTrnPostingType"]) or "",

                        debit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "1" else Decimal("0.00"),
                        credit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "0" else Decimal("0.00"),
                        interest_rate = safe_decimal(interest_rate)
                    )
                    # obj = AmountDebitTransaction(
                    #     company=company_obj,
                    #     trn_id=str(data["TrnId"]) or "",
                    #     lease=leases_dict.get(str(data["TrnOprLeasingOperationPrjId"])),
                    #     process_group_id=str(data["TrnPostingGroupId"]) or "",
                    #     process_group=str(data["JrnStpPstGrpName"]) or "",
                    #     due_date=make_aware(data["TrnDueDate"]) if data["TrnDueDate"] else None,
                    #     process_type=str(data["viewTrnPostingType"]) or "",
                    #     debit_amount=safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "1" else Decimal("0.00"),
                    #     credit_amount=safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "0" else Decimal("0.00"),
                    #     interest_rate=safe_decimal(interest_rate)
                    # )
                    #real amount
                    prev_obj = (adt_by_lease_and_process.get((obj.lease.lease_id,obj.process_group_id,obj.pk-1)))
                    if prev_obj:
                        obj.real_amount = (obj.debit_amount - obj.credit_amount) + prev_obj.real_amount
                    else:
                        obj.real_amount = obj.debit_amount - obj.credit_amount
                    obj.for_default_amount = obj.real_amount

                    #day
                    next_obj = (adt_by_lease_and_process.get((obj.lease.lease_id,obj.process_group_id,obj.pk+1)))
                    if next_obj and obj.real_amount > 0.4:
                        diff_date = to_date(next_obj.due_date) - to_date(obj.due_date)
                        obj.day = diff_date.days
                    elif not next_obj and obj.real_amount > 0.4:
                        diff_date = datetime.today().date() - obj.due_date.date()
                        obj.day = diff_date.days
                    else:
                        obj.day = 0

                    obj.adat_amount = obj.real_amount * obj.day
                    obj.default_amount = (obj.real_amount * (interest_rate/100) * obj.day) / Decimal("360")
                    obj.overdue_interest_rate = obj.default_amount + (obj.default_amount * Decimal("0.01"))
                    obj.save()
                    #new_objs.append(obj)
            #AmountDebitTransaction.objects.bulk_create(new_objs, batch_size=1000)
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")
    except Exception as e:
        print(e)
        traceback.print_exc()



@shared_task()
def fetch_amounts_and_debitss(company):
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
        # Tüm objeleri RAM'e almadan toplu silme işlemi
        AmountDebitTransaction.objects.all().delete()
        print("All AmountDebitTransaction objects deleted.")
        amount_debit_transactions = AmountDebitTransaction.objects.select_related("lease").filter()
        leases = Lease.objects.select_related().filter(contract__project__icontains="KIZILBÜK")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        amount_debit_transaction_by_code = {a.trn_id: a for a in amount_debit_transactions if a.trn_id}
        adt_by_lease_and_process = {(a.lease.lease_id, a.process_group_id, a.pk): a for a in amount_debit_transactions if a.lease.lease_id and a.process_group_id and a.pk}
        leases_dict = {l.lease_id: l for l in leases}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        conn = pyodbc.connect(connectionString)
        cursor = conn.cursor()

        records = fetch_amounts_and_debits_sql_bulk(cursor)

        external_data=[
            {
                "TrnId" : r.TrnId,
                "TrnOprLeasingOperationPrjId" : r.TrnOprLeasingOperationPrjId,
                "TrnPostingGroupId" : r.TrnPostingGroupId,
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
            current_progress = ((index + 1)/len(leases))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["TrnId"]):
                obj = (amount_debit_transaction_by_code.get(str(data["TrnId"])))
            else:
                obj = None

            if obj:
                pass
            else:
                new_obj_count += 1
                obj = AmountDebitTransaction.objects.select_related("lease").create(
                    company = company_obj,
                    trn_id = str(data["TrnId"]) or "",
                    lease = leases_dict.get(str(data["TrnOprLeasingOperationPrjId"])),
                    process_group_id = str(data["TrnPostingGroupId"]) or "",
                    process_group = str(data["JrnStpPstGrpName"]) or "",
                    due_date = make_aware(data["TrnDueDate"]) if data["TrnDueDate"] else None,
                    process_type = str(data["viewTrnPostingType"]) or "",

                    debit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "1" else Decimal("0.00"),
                    credit_amount = safe_decimal(data["TrnAmount"]) if str(data["TrnAmountType"]) == "0" else Decimal("0.00"),
                    interest_rate = safe_decimal(interest_rate)
                )

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
            ad_objs = AmountDebitTransaction.objects.select_related().filter(lease = obj).order_by("pk")

            for index,data in enumerate(ad_objs):
                #real amount
                prev_obj = (adt_by_lease_and_process.get((obj.lease.lease_id,obj.process_group_id,obj.pk-1)))
                if prev_obj:
                    obj.real_amount = (obj.debit_amount - obj.credit_amount) + prev_obj.real_amount
                else:
                    obj.real_amount = obj.debit_amount - obj.credit_amount
                obj.for_default_amount = obj.real_amount

                #day
                next_obj = (adt_by_lease_and_process.get((obj.lease.lease_id,obj.process_group_id,obj.pk+1)))
                if next_obj and obj.real_amount > 0.4:
                    diff_date = to_date(next_obj.due_date) - to_date(obj.due_date)
                    obj.day = diff_date.days
                elif not next_obj and obj.real_amount > 0.4:
                    diff_date = datetime.today().date() - obj.due_date.date()
                    obj.day = diff_date.days
                else:
                    obj.day = 0

                obj.adat_amount = obj.real_amount * obj.day
                obj.default_amount = (obj.real_amount * (interest_rate/100) * obj.day) / Decimal("360")
                obj.overdue_interest_rate = obj.default_amount + (obj.default_amount * Decimal("0.01"))
                obj.save()
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")
    except Exception as e:
        print(e)
        traceback.print_exc()