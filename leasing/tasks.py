from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io
import pyodbc
from decimal import Decimal

from .models import *
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency


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
            LopOpenDate
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
            }
            for r in records
        ]

        contracts = Contract.objects.select_related("status","company","quotation_obj","partner").all()
        statuses = Status.objects.select_related().all()
        partners = Partner.objects.select_related().all()
        quotations = Quotation.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        contract_by_code = {c.contract_id: c for c in contracts if c.contract_id}
        statuses_dict = {s.name: s for s in statuses}
        partners_dict = {p.crm_code: p for p in partners}
        quotations_dict = {q.code: q for q in quotations}

        previous_progress = 0
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
                
                obj.save()
            else:
                print(f"{str(data["ContractHeaderId"])} - {data["CustomerId"]}: ")
                Contract.objects.create(
                    company = company_obj,
                    contract_id = str(data["ContractHeaderId"]) or "",
                    code = str(data["ContractHeaderCode"]) or "",
                    partner = partners_dict.get(str(data["CustomerId"])),
                    quotation = quotations_dict.get(str(data["QuotationHeaderId"])),
                    committe = str(data["CommitteeName"]) or "",
                    credit_type = str(data["CreditTypeName"]) or "",
                    customer_representative = str(data["CustomerRepresentative"]) or "",
                    supplier = data["Vendor"] or "",
                    project = data["Project"] or "",
                    status = statuses_dict.get(normalize(data["SubStatuteName"])),
                    lop_open_date = make_aware(data["LopOpenDate"]) if data["LopOpenDate"] else None
                )
    except Exception as e:
        print(e)

@shared_task()
def fix_installments(lease_code):
    obj = Lease.objects.select_related("contract").filter(code = lease_code).first()

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
        
        SQL_QUERY = f'''
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

                (
                    CASE 
                        WHEN (
                            lopStatu.RiskIncludingTypeId = 6 
                            AND TrnLedgerStatu = 10 
                            AND (
                                (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                                OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                            )
                            AND TrnDueDate <= '20250703'
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
                                    AND TrnDueDate <= '20250703'
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
                        AND TrnDueDate <= '20250703' 
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
                        AND TrnDueDate <= '20250703' 
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                )
                AND TrnAccountType = 11 
                AND TrnAccountId <> 0 
                AND TrnDueDate <= CONVERT(DATETIME, '2025-7-3', 102)
                AND TrnOprContractId = {int(obj.contract.contract_id) if obj else 0}
                --AND JrnStpPstGrpName = 'Kira'

            ORDER BY 
                TrnDueDate

        '''

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()
        external_data=[
            {   
                "type" : r.TrnAmountType,
                "amount" : r.TrnAmount,
                "due_date" : r.TrnDueDate,
                "group" : r.JrnStpPstGrpName,
                "posting_type" : r.viewTrnPostingType,
                "document_no" : r.TrnReturnDocumentNo
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
            installment_obj = Installment.objects.select_related().filter(lease = obj, payment_date = gosterilecek_tarih).first()
            installment_obj.overdue_amount = Decimal(str(b['amount']))
            installment_obj.save()
            #print(f"Kira Planı: {installment_obj.lease.code} - Ödeme Tarihi: {installment_obj.payment_date} - Sıra No: {installment_obj.sequency}")
            #print(f"Belge No: {belge or '[belgesiz]'}, Vade: {gosterilecek_tarih}, Kalan Borç: {b['amount']}")
        #print(f"Toplam Borç: {toplam_borc}")

    except Exception as e:
        print(e)
    
