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
def fix_contracts(company):
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