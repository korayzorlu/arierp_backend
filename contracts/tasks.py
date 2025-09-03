from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.utils.timezone import make_aware

import pandas as pd
import io
import pyodbc

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal

@shared_task()
def fetch_contracts(company):
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
        SELECT ContractHeaderId,
            ContractHeaderCode,
            CustomerId,
            QuotationHeaderId,
            CommitteeName,
            CreditTypeName,
            CustomerRepresentative,
            Vendor,
            Project,
            SubStatuteName,
            LopOpenDate,
            CurrencyCode
        FROM ContractHeaderLightList
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "ContractHeaderId" : r.ContractHeaderId,
                "ContractHeaderCode" : r.ContractHeaderCode,
                "CustomerId" : r.CustomerId,
                "QuotationHeaderId" : r.QuotationHeaderId,
                "CommitteeName" : r.CommitteeName,
                "CreditTypeName" : r.CreditTypeName,
                "CustomerRepresentative" : r.CustomerRepresentative,
                "Vendor" : r.Vendor,
                "Project" : r.Project,
                "SubStatuteName" : r.SubStatuteName,
                "LopOpenDate" : r.LopOpenDate,
                "CurrencyCode" : r.CurrencyCode,
            }
            for r in records
        ]

        contracts = Contract.objects.select_related("status","company","quotation_obj","partner").all()
        statuses = Status.objects.select_related().all()
        partners = Partner.objects.select_related().all()
        quotations = Quotation.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        contract_by_code = {c.contract_id: c for c in contracts if c.contract_id}
        statuses_dict = {s.name: s for s in statuses}
        partners_dict = {p.crm_code: p for p in partners}
        quotations_dict = {q.code: q for q in quotations}
        currencies_dict = {c.code: c for c in currencies}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["ContractHeaderId"]):
                obj = (contract_by_code.get(str(data["ContractHeaderId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.contract_id = str(data["ContractHeaderId"]) or ""
                obj.code = str(data["ContractHeaderCode"]) or ""
                obj.partner = partners_dict.get(str(data["CustomerId"]))
                obj.quotation_obj = quotations_dict.get(str(data["QuotationHeaderId"]))
                obj.committe = str(data["CommitteeName"]) or ""
                obj.credit_type = str(data["CreditTypeName"]) or ""
                obj.customer_representative = str(data["CustomerRepresentative"]) or ""
                obj.supplier = data["Vendor"] or ""
                obj.project = data["Project"] or ""
                obj.status = statuses_dict.get(normalize(data["SubStatuteName"]))
                obj.lop_open_date = make_aware(data["LopOpenDate"]) if data["LopOpenDate"] else None
                obj.currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"])
                obj.save()
            else:
                new_obj_count += 1
                Contract.objects.create(
                    company = company_obj,
                    contract_id = str(data["ContractHeaderId"]) or "",
                    code = str(data["ContractHeaderCode"]) or "",
                    partner = partners_dict.get(str(data["CustomerId"])),
                    quotation_obj = quotations_dict.get(str(data["QuotationHeaderId"])),
                    committe = str(data["CommitteeName"]) or "",
                    credit_type = str(data["CreditTypeName"]) or "",
                    customer_representative = str(data["CustomerRepresentative"]) or "",
                    supplier = data["Vendor"] or "",
                    project = data["Project"] or "",
                    status = statuses_dict.get(normalize(data["SubStatuteName"])),
                    lop_open_date = make_aware(data["LopOpenDate"]) if data["LopOpenDate"] else None,
                    currency = currencies_dict.get("TRY" if data["CurrencyCode"] == "TL" else data["CurrencyCode"])
                )
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")
    except Exception as e:
        print(e)

@shared_task()
def fetch_contract_payments(company):
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
            SELECT DISTINCT
                0 AS Trn_Temp_RevenueCheckColumn,
                TrnId,
                TrnFromToType AS TrnFromToType_HIDDEN,
                TrnFromLedgerAccountId AS TrnFromLedgerAccountId_HIDDEN,
                TrnFromTradeAccountCode AS TrnFromTradeAccountCode_HIDDEN,
                TrnFromId = CASE TrnFromToType
                    WHEN 10 THEN tatFrom.AccTypUniqueId
                    WHEN 20 THEN LedgerAccount.AccountCode
                    ELSE ''
                END,
                AccountCode AS TrnFromLedgerAccountId_AC,
                AccountName AS TrnFromLedgerAccountId_AN,
                tatFrom.AccTypUniqueId AS TrnFromTradeAccountCode,
                e1.JrnStpEnumDescription AS viewTrnFromToType,
                e2.JrnStpEnumDescription AS viewTrnPostingType,
                TrnPostingType,
                '' AS Status,
                1 AS StatusId,
                JrnStpPstGrpName AS JrnStpPstGrpName,
                ch.ContractHeaderCode AS TrnOprContractId,
                TrnAccountCode,
                ta.AccName,
                tat.AccTypUniqueId AS OPR_AccTypUniqueId,
                tat.AccName AS OPR_AccName,
                TrnDate,
                TrnDueDate,
                TrnAmountTypeDebit = CASE TrnAmountType WHEN 1 THEN TrnAmount ELSE 0 END,
                TrnAmountTypeCredit = CASE TrnAmountType WHEN 0 THEN TrnAmount ELSE 0 END,
                TrnCurrencyCode,
                TrnAmountTypeLocalDebit = CASE TrnAmountType WHEN 1 THEN TrnAmountLocal ELSE 0 END,
                TrnAmountTypeLocalCredit = CASE TrnAmountType WHEN 0 THEN TrnAmountLocal ELSE 0 END,
                TrnExchangeRateLocal,
                TrnLegalExchangeRateLocal_TEMP = CASE
                    WHEN TrnLegalExchangeRateLocal = TrnExchangeRateLocal THEN ''
                    ELSE 'X'
                END,
                TrnDescription,
                TrnIsPlanned + TrnReturnValueId AS TrnIsPlanned,
                TrnIsPlanned_INFO = CASE TrnSourceType
                    WHEN 3 THEN 'Banka Otomasyonu'
                    WHEN 31 THEN 'ATS Banka Oto.'
                    WHEN 32 THEN 'BTS Banka Oto.'
                    WHEN 33 THEN 'ZİNCİRLİKUYU Banka Oto.'
                    WHEN 2 THEN 'Aktarım Datası'
                    WHEN 80 THEN 'Otomatik Tahsilat'
                    WHEN 60 THEN 'EFT'
                    WHEN 90 THEN 'Satıcı Avansı Tahsilatı'
                    ELSE CASE TrnIsPlanned
                        WHEN 1 THEN 'Planlanmış'
                        ELSE CASE TrnReturnValueId
                            WHEN 0 THEN 'Elle Girilmiş'
                            ELSE 'Modülden Gelmiş'
                        END
                    END
                END,
                userx.NameSurname AS CreatedUserId,
                TrnReturnDocumentNo,
                TrnCommittedRefId
            FROM TradeTransaction (NOLOCK)
            LEFT JOIN FoundationUserList userx (NOLOCK)
                ON (
                    CASE TrnCommittedRefId
                        WHEN 0 THEN TrnUserId
                        ELSE (
                            SELECT subTT.TrnUserId
                            FROM TradeTransaction subTT (NOLOCK)
                            WHERE subTT.TrnId = TradeTransaction.TrnCommittedRefId
                        )
                    END
                ) = userx.UserId
            LEFT JOIN JournalSetupEnums e1 (NOLOCK)
                ON TrnFromToType = e1.JrnStpEnumValue AND e1.JrnStpEnumType = 80
            LEFT JOIN JournalSetupEnums e2 (NOLOCK)
                ON TrnPostingType = e2.JrnStpEnumValue AND e2.JrnStpEnumType = 50
            LEFT JOIN LedgerAccount (NOLOCK)
                ON TrnFromLedgerAccountId = LedgerAccount.AccountId
            LEFT JOIN ContractHeader ch (NOLOCK)
                ON TrnOprContractId = ch.ContractHeaderId
            LEFT JOIN TradeAccount ta (NOLOCK)
                ON TrnAccountId = ta.AccId
            LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK)
                ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
            LEFT JOIN TradeAccountAndTypeComboList tat (NOLOCK)
                ON TrnOprCustomerId = tat.AccCrmId AND tat.AccTypType = 11
            LEFT JOIN TradeAccountTypes tatFrom (NOLOCK)
                ON TrnFromTradeAccountCode = tatFrom.AccTypUniqueId
                AND tatFrom.AccTypType = 31
                AND TrnFromToType = 10
            WHERE
                TrnDummy = 0
                AND (
                    TrnIsDeleted NOT IN (6, 4, 2, 8, 1)
                    OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
                )
                AND TrnAccountType IN (21, 11, 1)
                --AND TrnDate >= CONVERT(DATETIME, '2015-7-4', 102)
                --AND TrnDate <= CONVERT(DATETIME, '2025-7-28', 102)
                --AND TrnOprContractId = 41727
                AND TrnLayer = 1
                AND TrnLedgerStatu = 50
                AND ISNULL(TrnFromToType, 0) <> 0
                AND TrnTemplateType <> 0
                AND TrnAmountType = 0
                AND TrnPostingType IN (221, 211, 101, 102, 103, 931, 482)
            ORDER BY
                TrnDueDate,
                AccountName;
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "TrnOprContractId" : r.TrnOprContractId,
                "TrnId" : r.TrnId,
                "TrnFromId" : r.TrnFromId,
                "TrnFromLedgerAccountId_AC" : r.TrnFromLedgerAccountId_AC,
                "TrnFromLedgerAccountId_AN" : r.TrnFromLedgerAccountId_AN,
                "TrnFromTradeAccountCode" : r.TrnFromTradeAccountCode,
                "viewTrnFromToType" : r.viewTrnFromToType,
                "viewTrnPostingType" : r.viewTrnPostingType,
                "JrnStpPstGrpName" : r.JrnStpPstGrpName,
                "TrnAccountCode" : r.TrnAccountCode,
                "AccName" : r.AccName,
                "TrnDate" : r.TrnDate,
                "TrnDueDate" : r.TrnDueDate,
                "TrnAmountTypeDebit" : r.TrnAmountTypeDebit,
                "TrnAmountTypeCredit" : r.TrnAmountTypeCredit,
                "TrnCurrencyCode" : r.TrnCurrencyCode,
                "TrnAmountTypeLocalDebit" : r.TrnAmountTypeLocalDebit,
                "TrnAmountTypeLocalCredit" : r.TrnAmountTypeLocalCredit,
                "TrnExchangeRateLocal" : r.TrnExchangeRateLocal,
                "CreatedUserId" : r.CreatedUserId,
                "TrnDescription" : r.TrnDescription,
            }
            for r in records
        ]

        contract_payments = ContractPayment.objects.select_related("company","contract","currency").all()
        contracts = Contract.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        contract_payment_by_code = {c.trn_id: c for c in contract_payments if c.trn_id}
        contracts_dict = {c.code: c for c in contracts}
        currencies_dict = {c.code: c for c in currencies}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")
            
            if str(data["TrnId"]):
                obj = (contract_payment_by_code.get(str(data["TrnId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.contract = contracts_dict.get(str(data["TrnOprContractId"]))
                obj.trn_id = str(data["TrnId"]) or ""
                obj.trn_from_id = str(data["TrnFromId"]) or ""
                obj.ledger_account_id = str(data["TrnFromLedgerAccountId_AC"]) or ""
                obj.ledger_account_name = str(data["TrnFromLedgerAccountId_AN"]) or ""
                obj.trade_account_code = str(data["TrnFromTradeAccountCode"]) or ""
                obj.type = str(data["viewTrnFromToType"]) or ""
                obj.posting_type = str(data["viewTrnPostingType"]) or ""
                obj.group_name = str(data["JrnStpPstGrpName"]) or ""
                obj.account_code = str(data["TrnAccountCode"]) or ""
                obj.account_name = str(data["AccName"]) or ""
                obj.date = data["TrnDate"].date() if data["TrnDate"] else None
                obj.due_date = data["TrnDueDate"].date() if data["TrnDueDate"] else None
                obj.debit_amount = safe_decimal(data["TrnAmountTypeDebit"])
                obj.credit_amount = safe_decimal(data["TrnAmountTypeCredit"])
                obj.local_debit_amount = safe_decimal(data["TrnAmountTypeLocalDebit"])
                obj.local_credit_amount = safe_decimal(data["TrnAmountTypeLocalCredit"])
                obj.currency = currencies_dict.get("TRY" if data["TrnCurrencyCode"] == "TL" else data["TrnCurrencyCode"])
                obj.exchange_rate = safe_decimal(data["TrnExchangeRateLocal"])
                obj.description = str(data["TrnDescription"]) or ""
                obj.user_name = str(data["CreatedUserId"]) or ""
                obj.save()
            else:
                if data["TrnOprContractId"] and contracts_dict.get(str(data["TrnOprContractId"])):
                    new_obj_count += 1
                    ContractPayment.objects.create(
                        company = company_obj,
                        contract = contracts_dict.get(str(data["TrnOprContractId"])),
                        trn_id = str(data["TrnId"]) or "",
                        trn_from_id = str(data["TrnFromId"]) or "",
                        ledger_account_id = str(data["TrnFromLedgerAccountId_AC"]) or "",
                        ledger_account_name = str(data["TrnFromLedgerAccountId_AN"]) or "",
                        trade_account_code = str(data["TrnFromTradeAccountCode"]) or "",
                        type = str(data["viewTrnFromToType"]) or "",
                        posting_type = str(data["viewTrnPostingType"]) or "",
                        group_name = str(data["JrnStpPstGrpName"]) or "",
                        account_code = str(data["TrnAccountCode"]) or "",
                        account_name = str(data["AccName"]) or "",
                        date = data["TrnDate"].date() if data["TrnDate"] else None,
                        due_date = data["TrnDueDate"].date() if data["TrnDueDate"] else None,
                        debit_amount = safe_decimal(data["TrnAmountTypeDebit"]),
                        credit_amount = safe_decimal(data["TrnAmountTypeCredit"]),
                        local_debit_amount = safe_decimal(data["TrnAmountTypeLocalDebit"]),
                        local_credit_amount = safe_decimal(data["TrnAmountTypeLocalCredit"]),
                        currency = currencies_dict.get("TRY" if data["TrnCurrencyCode"] == "TL" else data["TrnCurrencyCode"]),
                        exchange_rate = safe_decimal(data["TrnExchangeRateLocal"]),
                        description = str(data["TrnDescription"]) or "",
                        user_name = str(data["CreatedUserId"]) or "",
                    )
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contract payments.")
    except Exception as e:
        print(e)

@shared_task()
def fetch_contract_projects(company):
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
        SELECT 
            v.CustomerId AS VendorId,
            c.ContractHeaderId AS ContractHeaderId
        FROM 
            dbo.QuotationLine l

            RIGHT JOIN dbo.InventoryStockCode isc 
                ON l.StockCodeId = isc.StockCodeId

            LEFT JOIN dbo.CrmCustomerWithTypesLight v 
                ON l.VendorId = v.CustomerId

            LEFT JOIN dbo.ContractHeaderLightList c 
                ON l.QuotationHeaderId = c.QuotationHeaderId
        WHERE  
            l.Deleted = 0 
            AND l.ItemType = 0
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "VendorId" : r.VendorId,
                "ContractHeaderId" : r.ContractHeaderId,
            }
            for r in records
        ]

        contracts = Contract.objects.select_related("project_obj","company").all()
        vendors = Partner.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        contract_by_code = {c.contract_id: c for c in contracts if c.contract_id}
        vendors_dict = {p.crm_code: p for p in vendors}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["ContractHeaderId"]):
                obj = (contract_by_code.get(str(data["ContractHeaderId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.vendor = vendors_dict.get(str(data["VendorId"]))
                obj.save()
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")
    except Exception as e:
        print(e)


@shared_task()
def fetch_warning_notices(company):
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
            SELECT RiskDocumentId,
                RiskHeaderId,
                CustomerId,
                ContractHeaderId,
                OrgContractHeaderId,
                Debit,
                ProcessStartDate,
                DailyWagesDate,
                ServiceDate,
                OfficialCancellationDate,
                Paid,
                Diff,
                State,
                ApprovalState,
                ResultId,
                PROCESS_SITUATION_ID
                FROM RiskDocumentWarningFollowListBaseLPDDOR
                WHERE
                    (PROCESS_SITUATION_ID is null or ResultId in (0,1,2)) 
                    AND 1=1
                    --AND CustomerId=29308
                    AND ResultId in (0,1) 
        """

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "RiskDocumentId" : r.RiskDocumentId,
                "RiskHeaderId" : r.RiskHeaderId,
                "CustomerId" : r.CustomerId,
                "ContractHeaderId" : r.ContractHeaderId,
                "OrgContractHeaderId" : r.OrgContractHeaderId,
                "Debit" : r.Debit,
                "ProcessStartDate" : r.ProcessStartDate,
                "DailyWagesDate" : r.DailyWagesDate,
                "ServiceDate" : r.ServiceDate,
                "OfficialCancellationDate" : r.OfficialCancellationDate,
                "Paid" : r.Paid,
                "Diff" : r.Diff,
                "State" : r.State,
                "ApprovalState" : r.ApprovalState,
            }
            for r in records
        ]

        warning_notices = WarningNotice.objects.select_related("company","contract","contract__currency").all()
        warning_notices.delete()
        contracts = Contract.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        warning_notice_by_code = {c.document_id: c for c in warning_notices if c.document_id}
        contracts_dict = {c.code: c for c in contracts}

        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")
            
            if str(data["RiskDocumentId"]):
                obj = (warning_notice_by_code.get(str(data["RiskDocumentId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.contract = contracts_dict.get(str(data["ContractHeaderId"]))
                obj.document_id = str(data["RiskDocumentId"]) or ""
                obj.risk_id = str(data["RiskHeaderId"]) or ""
                obj.customer_id = str(data["CustomerId"]) or ""
                obj.debit_amount = safe_decimal(data["Debit"])
                obj.daily_wages_date = data["DailyWagesDate"].date() if data["DailyWagesDate"] else None
                obj.process_start_date = data["ProcessStartDate"].date() if data["ProcessStartDate"] else None
                obj.service_date = data["ServiceDate"].date() if data["ServiceDate"] else None
                obj.official_cancellation_date = data["OfficialCancellationDate"].date() if data["OfficialCancellationDate"] else None
                obj.paid = safe_decimal(data["Paid"])
                obj.diff = safe_decimal(data["Diff"])
                obj.state = str(data["State"]) or ""
                obj.approval_state = str(data["ApprovalState"]) or ""
                obj.save()
            else:
                if data["ContractHeaderId"] and contracts_dict.get(str(data["ContractHeaderId"])):
                    new_obj_count += 1
                    WarningNotice.objects.create(
                        company = company_obj,
                        contract = contracts_dict.get(str(data["ContractHeaderId"])),
                        document_id = str(data["RiskDocumentId"]) or "",
                        risk_id = str(data["RiskHeaderId"]) or "",
                        customer_id = str(data["CustomerId"]) or "",
                        debit_amount = safe_decimal(data["Debit"]),
                        daily_wages_date = data["DailyWagesDate"].date() if data["DailyWagesDate"] else None,
                        process_start_date = data["ProcessStartDate"].date() if data["ProcessStartDate"] else None,
                        service_date = data["ServiceDate"].date() if data["ServiceDate"] else None,
                        official_cancellation_date = data["OfficialCancellationDate"].date() if data["OfficialCancellationDate"] else None,
                        paid = safe_decimal(data["Paid"]),
                        diff = safe_decimal(data["Diff"]),
                        state = str(data["State"]) or "",
                        approval_state = str(data["ApprovalState"]) or "",
                    )
        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for warning notices.")
    except Exception as e:
        print(e)     