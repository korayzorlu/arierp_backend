from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings

import pyodbc
import os

from datetime import datetime
import pandas as pd
import io
import os
import random
import string

from accounting.models import *
from common.models import Status
from partners.models import Partner
from common.utils.common_utils import normalize,safe_decimal

def fetch_trial_balances_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "accounting","sql","mizan.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        trial_balances = TrialBalance.objects.select_related("company","currency","partner").filter(company__id=int(company))
        partners = Partner.objects.select_related().filter(company__id=int(company))
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        trial_balance_by_code = {t.account_id: t for t in trial_balances if t.account_id}
        partners_dict = {p.crm_code: p for p in partners}
        currencies_dict = {c.code: c for c in currencies}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.AccountId):
                    obj = (trial_balance_by_code.get(str(data.AccountId)))
                else:
                    obj = None

                if obj:
                    obj.account_id = str(data.AccountId) or ""
                    obj.account_code = str(data.AccountCode) or ""
                    obj.account_code_trim = str(data.AccountCodeTrim) or ""
                    obj.account_name = str(data.AccountName) or ""  
                    obj.partner = partners_dict.get(str(data.CRMCode))
                    obj.balance_account_type = str(data.BalanceAccountType) or "" 
                    obj.currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode)
                    obj.balance_debit = safe_decimal(data.BalanceDebit)
                    obj.balance_credit = safe_decimal(data.BalanceCredit)
                    obj.total_debit = safe_decimal(data.TotalDebit)
                    obj.total_credit = safe_decimal(data.TotalCredit)
                    obj.balance_debit_alternate = safe_decimal(data.BalanceDebitAlternate)
                    obj.balance_credit_alternate = safe_decimal(data.BalanceCreditAlternate)
                    obj.total_debit_alternate = safe_decimal(data.TotalDebitAlternate)
                    obj.total_credit_alternate = safe_decimal(data.TotalCreditAlternate)
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(TrialBalance(
                        company = company_obj,
                        account_id = str(data.AccountId) or "",
                        account_code = str(data.AccountCode) or "",
                        account_code_trim = str(data.AccountCodeTrim) or "",
                        account_name = str(data.AccountName) or "",
                        partner = partners_dict.get(str(data.CRMCode)),
                        balance_account_type = str(data.BalanceAccountType) or "",
                        currency = currencies_dict.get("TRY" if data.CurrencyCode == "TL" else data.CurrencyCode),
                        balance_debit = safe_decimal(data.BalanceDebit),
                        balance_credit = safe_decimal(data.BalanceCredit),
                        total_debit = safe_decimal(data.TotalDebit),
                        total_credit = safe_decimal(data.TotalCredit),
                        balance_debit_alternate = safe_decimal(data.BalanceDebitAlternate),
                        balance_credit_alternate = safe_decimal(data.BalanceCreditAlternate),
                        total_debit_alternate = safe_decimal(data.TotalDebitAlternate),
                        total_credit_alternate = safe_decimal(data.TotalCreditAlternate)
                    ))
                    create_progress += 1
            if update_objs:
                TrialBalance.objects.bulk_update(update_objs, [
                    "account_id","account_code","account_code_trim","account_name","partner",
                    "balance_account_type","currency","balance_debit","balance_credit",
                    "total_debit","total_credit","balance_debit_alternate","balance_credit_alternate",
                    "total_debit_alternate","total_credit_alternate"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                TrialBalance.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} mizan güncellendi.")
        print(f"Toplam {create_progress} mizan oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)