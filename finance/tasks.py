from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.conf import settings

import pandas as pd
import io
import pyodbc
import os
import traceback
import logging

from .models import *
from users.models import User
from contracts.models import *
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from .utils import fetch_finekra_currencies,fetch_finekra_banks,post_finekra_bank_accounts,fetch_finekra_bank_accounts,delete_finekra_bank_account,put_finekra_bank_accounts,get_finmaks_bank_accounts
from django.db.models import Q

@shared_task()
def fetch_partner_advances(company):
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
        
        SQL_PATH = os.path.join(settings.BASE_DIR, "finance","sql","musteri_avanslari.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        
        records = cursor.fetchall()

        external_data=[
            {
                "TrnAccountCrmId" : r.TrnAccountCrmId,
                "TrnAmountLocal" : r.TrnAmountLocal,
            }
            for r in records
        ]

        partners = Partner.objects.select_related().all()
        partners.update(advance_amount=0)
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        partner_by_code = {p.crm_code: p for p in partners if p.crm_code}
        
        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,data in enumerate(external_data):
            current_progress = ((index + 1)/len(external_data))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            if str(data["TrnAccountCrmId"]):
                obj = (partner_by_code.get(str(data["TrnAccountCrmId"])))
            else:
                obj = None

            if obj:
                old_obj_count += 1
                obj.advance_amount = safe_decimal(data["TrnAmountLocal"])
                obj.save()

                print(obj.advance_amount)

        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")

    except Exception as e:
        traceback.print_exc()

@shared_task()
def fetch_finmaks_bank_accounts(company):
    USERNAME = settings.FINMAKS_USERNAME
    PASSWORD = settings.FINMAKS_PASSWORD
    INSTITUTION_CODE = "0001"
    INSTITUTION_ID = 1

    logger = logging.getLogger("django")
    try:
        bank_accounts = get_finmaks_bank_accounts(USERNAME,PASSWORD,INSTITUTION_CODE,INSTITUTION_ID)

        finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().all()
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        finmaks_bank_account_by_code = {b.bank_account_id: b for b in finmaks_bank_accounts if b.bank_account_id}
        currencies_dict = {c.code: c for c in currencies}
        
        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,bank_account in enumerate(bank_accounts):
            current_progress = ((index + 1)/len(bank_accounts))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            obj = (finmaks_bank_account_by_code.get(str(bank_account["BankAccountId"])))
            if obj:
                if bank_account["Currency"] == "TL" or bank_account["Currency"] == "YTL":
                    currency = "TRY"
                else:
                    currency = bank_account["Currency"]
                obj.bank_account_id = str(bank_account["BankAccountId"]) or ""
                obj.iban = str(bank_account["IBAN"]) or ""
                obj.account_no = str(bank_account["AccountNo"]) or ""
                obj.branch_code = str(bank_account["BranchCode"]) or ""
                obj.branch_name = str(bank_account["BranchName"]) or ""
                obj.finmaks_account_type = str(bank_account["FinmaksAccountType"]) or ""
                obj.balance = safe_decimal(bank_account["Balance"].replace(",", ""))
                obj.available_balance = safe_decimal(bank_account["AvailableBalance"].replace(",", ""))
                obj.over_draft = safe_decimal(bank_account["OverDraft"].replace(",", ""))
                obj.credit_risk = safe_decimal(bank_account["CreditRisk"].replace(",", ""))
                obj.blocked_balance = safe_decimal(bank_account["BlockedBalance"].replace(",", ""))
                obj.credit_limit = safe_decimal(bank_account["CreditLimit"].replace(",", ""))
                obj.currency = currencies_dict.get(currency)
                obj.currency_type = str(bank_account["CurrencyType"]) or ""
                obj.bank_name = str(bank_account["BankName"]) or ""
                obj.bank_code = str(bank_account["BankCode"]) or ""
                obj.bank_integration_info_id = str(bank_account["BankIntegrationInfoId"]) or ""
                obj.last_read_time = datetime.fromisoformat(bank_account["LastReadTime"])
                obj.status = bank_account["Status"]
                obj.save()
            else:
                if obj["Currency"] == "TL" or bank_account["Currency"] == "YTL":
                    currency = "TRY"
                else:
                    currency = bank_account["Currency"]
                FinmaksBankAccount.objects.create(
                    company = company_obj,
                    bank_account_id = str(bank_account["BankAccountId"]) or "",
                    iban = str(bank_account["IBAN"]) or "",
                    account_no = str(bank_account["AccountNo"]) or "",
                    branch_code = str(bank_account["BranchCode"]) or "",
                    branch_name = str(bank_account["BranchName"]) or "",
                    finmaks_account_type = str(bank_account["FinmaksAccountType"]) or "",
                    balance = safe_decimal(bank_account["Balance"].replace(",", "")),
                    available_balance = safe_decimal(bank_account["AvailableBalance"].replace(",", "")),
                    over_draft = safe_decimal(bank_account["OverDraft"].replace(",", "")),
                    credit_risk = safe_decimal(bank_account["CreditRisk"].replace(",", "")),
                    blocked_balance = safe_decimal(bank_account["BlockedBalance"].replace(",", "")),
                    credit_limit = safe_decimal(bank_account["CreditLimit"].replace(",", "")),
                    currency = currencies_dict.get(currency),
                    currency_type = str(bank_account["CurrencyType"]) or "",
                    bank_name = str(bank_account["BankName"]) or "",
                    bank_code = str(bank_account["BankCode"]) or "",
                    bank_integration_info_id = str(bank_account["BankIntegrationInfoId"]) or "",
                    last_read_time = datetime.fromisoformat(bank_account["LastReadTime"]),
                    status = bank_account["Status"],
                )

        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")

    except Exception as e:
        traceback.print_exc()

@shared_task()
def post_finmaks_bank_accounts(company):
    try:
        finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        finmaks_bank_account_by_code = {f.bank_account_id: f for f in finmaks_bank_accounts if f.bank_account_id}
        
        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,obj in enumerate(finmaks_bank_accounts):
            current_progress = ((index + 1)/len(finmaks_bank_accounts))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            print(f"banka: {obj.bank_name} - banka kodu: {obj.bank_code}")

        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")

    except Exception as e:
        traceback.print_exc()

@shared_task()
def add_finekra_bank_accounts(company):
    try:
        finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().filter(
            Q(currency__isnull=False) &
            Q(finmaks_account_type="1") &
            Q(iban__isnull=False) &
            Q(iban__startswith="TR") &
            ~Q(iban="TR850001200962600053000709") &
            ~Q(iban="TR180001200962600058000422")
        )
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        finmaks_bank_account_by_code = {f.bank_account_id: f for f in finmaks_bank_accounts if f.bank_account_id}
        
        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,obj in enumerate(finmaks_bank_accounts):
            current_progress = ((index + 1)/len(finmaks_bank_accounts))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            print(f"banka: {obj.bank_name} - banka kodu: {obj.bank_code}")
            
            currencies = fetch_finekra_currencies()
            currency_id = next((item["id"] for item in currencies if item["code"] == obj.currency.code), None)
            banks = fetch_finekra_banks()
            bank_id = next((item["id"] for item in banks if item["code"] == obj.bank_code), None)

            payload = {
                "iban": obj.iban if obj.iban else None,
                "balance": float(obj.balance),
                "branchCode": obj.branch_code if obj.branch_code else None,
                "branchName": obj.branch_name if obj.branch_name else None,
                "accountNumber": obj.account_no if obj.account_no else None,
                "accountSuffix": None,
                "currencyId": int(currency_id) if currency_id else None,
                "description": None,
                "name": None,
                "type": 0,
                "dueDate": None,
                "interestRate": None,
                "isCalculated": True,
                "bankId": int(bank_id) if bank_id else None,
                "creditLimit": None,
                "lastQueryDate": obj.last_read_time.isoformat().replace("+00:00", "Z") if obj.last_read_time else None,
                "availableCreditLimit": None,
                "availableCreditBalance": float(obj.available_balance),
                "availableBalance": float(obj.available_balance),
                "openDate": None,
                "creditBalance": None,
                "blockedAmount": float(obj.blocked_balance),
            }

            response = post_finekra_bank_accounts(payload)

            print(f"{obj.bank_name} - {obj.bank_code} - {obj.iban} - {obj.account_no} - {obj.currency.code}")
            print(response)

            if response["status"] == "success":
                obj.finekra_bank_account_id = response["message"]
                obj.save()

        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")

    except Exception as e:
        traceback.print_exc()

@shared_task()
def update_finekra_bank_accounts(company):
    try:
        finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().filter(
            Q(currency__isnull=False) &
            Q(finmaks_account_type="1") &
            Q(iban__isnull=False) &
            Q(iban__startswith="TR") &
            ~Q(iban="TR850001200962600053000709") &
            ~Q(iban="TR180001200962600058000422")
        )
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        finmaks_bank_account_by_code = {f.bank_account_id: f for f in finmaks_bank_accounts if f.bank_account_id}
        
        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,obj in enumerate(finmaks_bank_accounts):
            current_progress = ((index + 1)/len(finmaks_bank_accounts))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                # print(f"{int(current_progress)} %")

            # print(f"banka: {obj.bank_name} - banka kodu: {obj.bank_code}")
            
            currencies = fetch_finekra_currencies()
            currency_id = next((item["id"] for item in currencies if item["code"] == obj.currency.code), None)
            banks = fetch_finekra_banks()
            bank_id = next((item["id"] for item in banks if item["code"] == obj.bank_code), None)

            payload = {
                "id": obj.finekra_bank_account_id if obj.finekra_bank_account_id else None,
                "iban": obj.iban if obj.iban else None,
                "balance": float(obj.balance),
                "branchCode": obj.branch_code if obj.branch_code else None,
                "branchName": obj.branch_name if obj.branch_name else None,
                "accountNumber": obj.account_no if obj.account_no else None,
                "accountSuffix": None,
                "currencyId": int(currency_id) if currency_id else None,
                "description": None,
                "name": None,
                "type": 0,
                "dueDate": None,
                "interestRate": None,
                "isCalculated": True,
                "bankId": int(bank_id) if bank_id else None,
                "creditLimit": None,
                "lastQueryDate": obj.last_read_time.isoformat().replace("+00:00", "Z") if obj.last_read_time else None,
                "availableCreditLimit": None,
                "availableCreditBalance": float(obj.available_balance),
                "availableBalance": float(obj.available_balance),
                "openDate": None,
                "creditBalance": None,
                "blockedAmount": float(obj.blocked_balance),
            }

            response = put_finekra_bank_accounts(payload)

            if response["status"] == "error":
                print(f"Error updating bank account {obj.bank_name} - {obj.bank_code} - {obj.iban} - {obj.account_no} - {obj.currency.code}: {response['message']}" )
        
        print("Successfully updated all bank accounts.")
        #     print(f"{obj.bank_name} - {obj.bank_code} - {obj.iban} - {obj.account_no} - {obj.currency.code}")
        #     print(response)

        # print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")

    except Exception as e:
        traceback.print_exc()

@shared_task()
def delete_finekra_bank_accounts(company):
    try:
        finmaks_bank_accounts = FinmaksBankAccount.objects.select_related().filter(currency__isnull=False,finmaks_account_type = "1",uuid="3f9561c1-49cd-49f5-81cb-a2194b4a072a")
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        finmaks_bank_account_by_code = {f.bank_account_id: f for f in finmaks_bank_accounts if f.bank_account_id}
        
        previous_progress = 0
        old_obj_count = 0
        new_obj_count = 0
        for index,obj in enumerate(finmaks_bank_accounts):
            current_progress = ((index + 1)/len(finmaks_bank_accounts))*100

            if current_progress - previous_progress >= 1:
                previous_progress = current_progress
                print(f"{int(current_progress)} %")

            print(f"banka: {obj.bank_name} - banka kodu: {obj.bank_code}")

            if obj.finekra_bank_account_id:
                response = delete_finekra_bank_account(obj.finekra_bank_account_id)

            print(f"{obj.bank_name} - {obj.bank_code} - {obj.iban} - {obj.account_no} - {obj.currency.code}")
            print(response)

        print(f"{old_obj_count} objects updated and {new_obj_count} objects created for contracts.")

    except Exception as e:
        traceback.print_exc()