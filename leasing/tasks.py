from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io
import pyodbc
from decimal import Decimal

from .models import *
from .utils import get_lease_status_value
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner

@shared_task()
def fix_leases(company):
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
        SELECT OperationProjectId,
            OperationProjectCode,
            ContractHeaderCode,
            TypeName,
            VatRate,
            ActivationDate,
            RiskIncludingTypeName,
            CurrencyCode,
            CustomerBaseCost,
            PaymentCount,
            AnnualRate,
            OperationBaseIRR,
            SubStatuteName,
            LeasingTypeName,
            ApplicationID,
            IS_LAST_PROJECT,
            CurrentRequest
        FROM LeasingOperationProjectList
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {   
                "OperationProjectId" : r.OperationProjectId,
                "OperationProjectCode" : r.OperationProjectCode,
                "ContractHeaderCode" : r.ContractHeaderCode,
                "TypeName" : r.TypeName,
                "VatRate" : r.VatRate,
                "ActivationDate" : r.ActivationDate,
                "RiskIncludingTypeName" : r.RiskIncludingTypeName,
                "CurrencyCode" : r.CurrencyCode,
                "CustomerBaseCost" : r.CustomerBaseCost,
                "PaymentCount" : r.PaymentCount,
                "AnnualRate" : r.AnnualRate,
                "OperationBaseIRR" : r.OperationBaseIRR,
                "SubStatuteName" : r.SubStatuteName,
                "LeasingTypeName" : r.LeasingTypeName,
                "ApplicationID" : r.ApplicationID,
                "IS_LAST_PROJECT" : r.IS_LAST_PROJECT,
                "CurrentRequest" : r.CurrentRequest,
                "IS_LAST_PROJECT" : r.IS_LAST_PROJECT,
            }
            for r in records
        ]

        leases = Lease.objects.select_related("status","company","contract","currency").all()
        contracts = Contract.objects.select_related().all()
        statuses = Status.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        lease_by_code = {l.lease_id: l for l in leases if l.lease_id}
        contracts_dict = {c.code: c for c in contracts}
        statuses_dict = {s.name: s for s in statuses}
        currencies_dict = {c.code: c for c in currencies}

        previous_progress = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["OperationProjectId"]):
                obj = (lease_by_code.get(str(data["OperationProjectId"])))
            else:
                obj = None

            if obj:
                obj.lease_id = str(data["OperationProjectId"]) or ""
                obj.code = str(data["OperationProjectCode"]) or ""
                obj.contract = contracts_dict.get(str(data["ContractHeaderCode"]))
                obj.type = str(data["TypeName"]) or ""
                obj.vat = safe_decimal(data["VatRate"])
                obj.activation_date = data["ActivationDate"].date() if data["ActivationDate"] else None
                obj.lease_status = get_lease_status_value(str(data["RiskIncludingTypeName"])) or None
                obj.currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"])
                obj.musteri_baz_maliyet = safe_decimal(data["CustomerBaseCost"])
                obj.vade = int(data["PaymentCount"]) or ""
                obj.leasing_rate = safe_decimal(data["AnnualRate"])
                obj.irr = safe_decimal(data["OperationBaseIRR"])
                obj.status = statuses_dict.get(normalize(data["SubStatuteName"]))
                obj.leasing_type = str(data["LeasingTypeName"]) or ""
                obj.application_no = str(data["ApplicationID"]) or ""
                obj.is_last_project = True if str(data["IS_LAST_PROJECT"]) == "1" else False
                obj.current_request = str(data["CurrentRequest"]) or ""
                obj.save()
            else:
                print(f"{str(data["OperationProjectCode"])} - {data["ContractHeaderCode"]}: ")
                Lease.objects.create(
                    company = company_obj,
                    lease_id = str(data["OperationProjectId"]) or "",
                    code = str(data["OperationProjectCode"]) or "",
                    contract = contracts_dict.get(str(data["ContractHeaderCode"])),
                    type = str(data["TypeName"]) or "",
                    vat = safe_decimal(data["VatRate"]),
                    activation_date = data["ActivationDate"].date() if data["ActivationDate"] else None,
                    lease_status = get_lease_status_value(str(data["RiskIncludingTypeName"])) or None,
                    currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"]),
                    musteri_baz_maliyet = safe_decimal(data["CustomerBaseCost"]),
                    vade = int(data["PaymentCount"]) or "",
                    leasing_rate = safe_decimal(data["AnnualRate"]),
                    irr = safe_decimal(data["OperationBaseIRR"]),
                    status = statuses_dict.get(normalize(data["SubStatuteName"])),
                    leasing_type = str(data["LeasingTypeName"]) or "",
                    application_no = str(data["ApplicationID"]) or "",
                    is_last_project = True if str(data["IS_LAST_PROJECT"]) == "1" else False,
                    current_request = str(data["CurrentRequest"]) or "",
                )
    except Exception as e:
        print(e)

@shared_task()
def fix_installments(company):
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
        SELECT OPERATIONPROJECTID,
            SequenceNo,
            PAYMENTDATE,
            VATRATE,
            VATAMOUNT,
            PAYMENT,
            TOTALPAYMENTAMOUNT,
            PRINCIPALDISPLAY,
            INTERESTDISPLAY,
            LeaseType
        FROM LOPPAYMENTDUELISTFORARI
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {   
                "OPERATIONPROJECTID" : r.OPERATIONPROJECTID,
                "SequenceNo" : r.SequenceNo,
                "PAYMENTDATE" : r.PAYMENTDATE,
                "VATRATE" : r.VATRATE,
                "VATAMOUNT" : r.VATAMOUNT,
                "PAYMENT" : r.PAYMENT,
                "TOTALPAYMENTAMOUNT" : r.TOTALPAYMENTAMOUNT,
                "PRINCIPALDISPLAY" : r.PRINCIPALDISPLAY,
                "INTERESTDISPLAY" : r.INTERESTDISPLAY,
                "LeaseType" : r.LeaseType,
            }
            for r in records
        ]

        installments = Installment.objects.select_related("lease").all()
        leases = Lease.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency is not None}
        leases_dict = {l.lease_id: l for l in leases}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["OPERATIONPROJECTID"]) and str(data["SequenceNo"]):
                obj = (installment_by_code.get((str(data["OPERATIONPROJECTID"]),int(data["SequenceNo"]))))
                if int(data["SequenceNo"]) == 0:
                    obj.delete()
                obj = None
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.lease = leases_dict.get(str(data["OPERATIONPROJECTID"]))
                obj.payment_date = data["PAYMENTDATE"].date() if data["PAYMENTDATE"] else None
                obj.vat = safe_decimal(data["VATRATE"])
                obj.vat_amount = safe_decimal(data["VATAMOUNT"])
                obj.payment = safe_decimal(data["PAYMENT"])
                obj.amount = safe_decimal(data["TOTALPAYMENTAMOUNT"])
                obj.principal = safe_decimal(data["PRINCIPALDISPLAY"])
                obj.interest = safe_decimal(data["INTERESTDISPLAY"])
                obj.sequency = int(data["SequenceNo"])
                obj.lease_type = data["LeaseType"] or ""
                obj.save()
            else:
                new_obj_count += 1
                Installment.objects.create(
                    company = company_obj,
                    lease = leases_dict.get(str(data["OPERATIONPROJECTID"])),
                    payment_date = data["PAYMENTDATE"].date() if data["PAYMENTDATE"] else None,
                    vat = safe_decimal(data["VATRATE"]),
                    vat_amount = safe_decimal(data["VATAMOUNT"]),
                    payment = safe_decimal(data["PAYMENT"]),
                    amount = safe_decimal(data["TOTALPAYMENTAMOUNT"]),
                    principal = safe_decimal(data["PRINCIPALDISPLAY"]),
                    interest = safe_decimal(data["INTERESTDISPLAY"]),
                    sequency = int(data["SequenceNo"]),
                    lease_type = data["LeaseType"] or ""
                )
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for installments.")
    except Exception as e:
        print(e)


@shared_task()
def fix_collections(company):
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

    leases = Lease.objects.select_related("contract").all()
    installments = Installment.objects.select_related("lease").all()

    installment_by_code = {(i.lease.lease_id, i.payment_date): i for i in installments if i.lease.lease_id and i.payment_date}

    previous_progress = 0
    for index,lease in enumerate(leases):
        current_progress = ((index + 1)/len(leases))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

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
                                AND TrnDueDate <= '20250721'
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
                                        AND TrnDueDate <= '20250721'
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
                    TrnDummy = 0 
                    AND (
                        TrnIsDeleted NOT IN (6, 4, 2, 8, 1) 
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
                            AND TrnDueDate <= '20250721' 
                            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                        )
                    )
                    AND (
                        ISNULL(xx.OperationProjectId_Count, 0) > 0 
                        OR (ISNULL(xx.OperationProjectId_Count, 0) = 0 AND TrnPostingType <> 126)
                    )
                    AND (
                        TrnLedgerStatu = 50 
                        OR (
                            lopStatu.RiskIncludingTypeId = 6 
                            AND TrnLedgerStatu = 10 
                            AND TrnPostingType >= 110 AND TrnPostingType <= 120 
                            AND TrnDueDate <= '20250721' 
                            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                        )
                    )
                    AND TrnAccountType = 11 
                    AND TrnAccountId <> 0 
                    AND TrnDueDate <= CONVERT(DATETIME, '2025-7-30', 102)
                    AND TrnOprContractId = {int(lease.contract.contract_id) if lease else 0}
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

            # for data in external_data:
            #     print(f"{data["type"]} - {data["amount"]} - {data["due_date"]} - {data["group"]} - {data["posting_type"]} - {data["document_no"]}")

            # result = {
            #     'type1': sum(item['amount'] for item in external_data if item['type'] == 1),
            #     'type0': sum(item['amount'] for item in external_data if item['type'] == 0)
            # }

            # print(result["type1"] - result["type0"])

            # from collections import defaultdict
            # data_by_contract = defaultdict(list)

            # previous_progress = 0
            # for index,d in enumerate(external_data):
            #     current_progress = ((index + 1)/len(external_data))*100

            #     if current_progress - previous_progress >= 1:
            #         previous_progress = current_progress
            #         print(f"external data: {int(current_progress)} %")
            #     data_by_contract[d["contract_id"]].append(d)

            # installments = Installment.objects.select_related("lease").all()

            # installment_by_code = {(i.lease.lease_id, i.payment_date): i for i in installments if i.lease.lease_id and i.payment_date}



            borclar = sorted([x for x in external_data if x['type'] == 1], key=lambda x: x['due_date'])
            tahsilatlar = sorted([x for x in external_data if x['type'] == 0], key=lambda x: x['due_date'])
            

            # Ödeme işlemi
            i = 0  # tahsilat index
            for borc in borclar:
                while borc['amount'] > 0 and i < len(tahsilatlar):
                    tahsilat = tahsilatlar[i]
                    if tahsilat['amount'] == 0:
                        i += 1
                        continue

                    odenecek = min(borc['amount'], tahsilat['amount'])
                    borc['amount'] -= odenecek
                    tahsilat['amount'] -= odenecek

                    if tahsilat['amount'] == 0:
                        i += 1  # sonraki tahsilata geç

            # Kalan borçları yazdırmadan önce belgeye göre 'Kira - Kira - Normal' tarihlerini bulalım
            def get_latest_kira_normal_due_date(document_no, data):
                if not document_no:
                    return None
                kira_normaller = [d['due_date'] for d in data 
                                if d['document_no'] == document_no and d['posting_type'] == 'Kira - Normal']
                if kira_normaller:
                    return max(kira_normaller).date()
                else:
                    return None

            kalan_borclar = [b for b in borclar if b['amount'] > 0]

            #print("🎯 Kalan Borçlar:")
            toplam_borc = Decimal("0")
            for b in kalan_borclar:
                belge = b['document_no']
                kira_normal_tarih = get_latest_kira_normal_due_date(belge, external_data)
                gosterilecek_tarih = kira_normal_tarih or b['due_date'].date()
                toplam_borc += b['amount']
                installment_obj = (installment_by_code.get((lease.lease_id,gosterilecek_tarih)))
                installment_obj.overdue_amount = Decimal(str(b['amount']))
                installment_obj.save()
                #print(f"Kira Planı: {installment_obj.lease.code} - Ödeme Tarihi: {installment_obj.payment_date} - Sıra No: {installment_obj.sequency}")
                #print(f"Belge No: {belge or '[belgesiz]'}, Vade: {gosterilecek_tarih}, Kalan Borç: {b['amount']}")
            #print(f"Toplam Borç: {toplam_borc}")

        except Exception as e:
            print(e)
        
@shared_task()
def fetch_leases_overdue_amount(company):
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
            SELECT
                TrnOprContractId,
                TrnOprLeasingOperationPrjId,
                TrnPostingGroupId,
                TrnCurrencyCode,

                SUM((
                    CASE
                        WHEN (
                            (lopStatu.RiskIncludingTypeId IN (6)
                                AND TrnLedgerStatu = 10
                                AND TrnPostingType BETWEEN 110 AND 120
                                AND TrnIsDeleted <> 9
                                AND TrnDueDate <= '20250723'
                                AND ISNULL(xx.OperationProjectId_Count, 0) = 0)
                            OR
                            (lopStatu.RiskIncludingTypeId IN (6)
                                AND TrnLedgerStatu = 10
                                AND TrnPostingType BETWEEN 110 AND 120
                                AND TrnIsDeleted <> 9
                                AND TrnDueDate <= '20250723'
                                AND ISNULL(xx.OperationProjectId_Count, 0) = 1)
                        )
                        THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                        ELSE TrnAmount
                    END
                ) * TrnAmountType) AS AmountDebit,

                SUM((
                    CASE
                        WHEN (
                            lopStatu.RiskIncludingTypeId = 6
                            AND TrnLedgerStatu = 10
                            AND (
                                (TrnIsDeleted <> 9 AND TrnPostingType BETWEEN 110 AND 120)
                                OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                            )
                            AND TrnDueDate <= '20250723'
                            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                        )
                        THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                        ELSE TrnAmount
                    END
                ) * (1 - TrnAmountType)) AS AmountCredit

            FROM TradeTransaction (NOLOCK)

            LEFT JOIN LeasingOperationProject lopStatu (NOLOCK)
                ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId

            LEFT JOIN (
                SELECT
                    kk.OperationProjectId AS OperationProject_Id,
                    COUNT(*) AS OperationProjectId_Count
                FROM LeasingOperationProject kk (NOLOCK)
                WHERE NOT (
                    kk.RiskIncludingTypeId IN (3, 6)
                    OR (kk.RiskIncludingTypeId IN (9, 5, 7) AND kk.OperationTypeId = 1)
                )
                GROUP BY kk.OperationProjectId
            ) xx ON xx.OperationProject_Id = lopStatu.OperationProjectId

            LEFT JOIN LeasingOperationProject lopX (NOLOCK)
                ON lopX.OperationProjectId = (
                    CASE
                        WHEN TrnOprRevisionLOPId <> 0 THEN TrnOprRevisionLOPId
                        ELSE TrnOprLeasingOperationPrjId
                    END
                )

            WHERE
                TrnDummy = 0
                AND (
                    CASE
                        WHEN TrnIsDeleted = 4
                            AND lopStatu.RiskIncludingTypeId = 7
                            AND (
                                SELECT lll.RiskIncludingTypeId
                                FROM LeasingOperationProject lll (NOLOCK)
                                WHERE lll.OperationProjectId = lopStatu.OperationProjectId
                            ) = 6 THEN 3

                        WHEN TrnIsDeleted = 4
                            AND lopStatu.RiskIncludingTypeId = 6
                            AND (
                                SELECT TOP 1 lll.RiskIncludingTypeId
                                FROM LOPRevisionJoinListOutPlan lll (NOLOCK)
                                WHERE (
                                    lll.OperationProjectId = TrnOprRevisionLOPId AND TrnOprRevisionLOPId <> 0
                                ) OR (
                                    lll.OperationProjectId = TrnOprLeasingOperationPrjId AND TrnOprRevisionLOPId = 0
                                )
                            ) = 7 THEN 3

                        ELSE TrnIsDeleted
                    END NOT IN (6, 4, 2, 8, 1)
                    OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
                )
                AND TrnPostingType NOT IN (461, 113)
                AND (
                    TrnLayer = 1
                    OR (
                        lopStatu.RiskIncludingTypeId IN (6, 7)
                        AND TrnLayer = 3
                        AND TrnPostingType BETWEEN 110 AND 120
                        AND TrnDueDate <= '20250723'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                    OR (
                        lopStatu.RiskIncludingTypeId = 7
                        AND TrnLayer = 3
                        AND TrnPostingType BETWEEN 110 AND 120
                        AND TrnDueDate <= '20250723'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 1
                    )
                )
                AND (
                    TrnLedgerStatu = 50
                    OR (
                        lopStatu.RiskIncludingTypeId IN (6, 7)
                        AND TrnLedgerStatu = 10
                        AND TrnPostingType BETWEEN 110 AND 120
                        AND TrnDueDate <= '20250723'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                    OR (
                        lopStatu.RiskIncludingTypeId = 7
                        AND TrnLedgerStatu = 10
                        AND TrnPostingType BETWEEN 110 AND 120
                        AND TrnDueDate <= '20250723'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 1
                    )
                )
                AND TrnAccountType = 11
                AND lopStatu.IS_LAST_PROJECT = 1
                AND TrnOprLeasingOperationPrjId <> 0
                AND NOT (
                    lopX.OperationTypeId = 1
                    AND lopX.RiskIncludingTypeId IN (9)
                    AND TrnPostingType BETWEEN 110 AND 120
                )
                --AND TrnOprLeasingOperationPrjId IN (55734, 75289)
                AND TrnDueDate <= CONVERT(DATETIME, '2025-7-23', 102)

            GROUP BY
                TrnOprContractId,
                TrnOprLeasingOperationPrjId,
                TrnPostingGroupId,
                TrnCurrencyCode;
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {   
                "TrnOprLeasingOperationPrjId" : r.TrnOprLeasingOperationPrjId,
                "AmountDebit" : r.AmountDebit,
                "AmountCredit" : r.AmountCredit,
            }
            for r in records
        ]

        leases = Lease.objects.select_related("status","company","contract","currency").all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        lease_by_code = {l.lease_id: l for l in leases if l.lease_id}

        previous_progress = 0
        old_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["TrnOprLeasingOperationPrjId"]):
                obj = (lease_by_code.get(str(data["TrnOprLeasingOperationPrjId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.paid = safe_decimal(data["AmountCredit"])
                obj.overdue_amount = safe_decimal(data["AmountDebit"]) - safe_decimal(data["AmountCredit"])
                obj.save()
        print(f"{old_obj_count} objects updated for contract leases.")
    except Exception as e:
        print(e)
