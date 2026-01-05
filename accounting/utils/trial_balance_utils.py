from django.http import JsonResponse
from django.utils.timezone import make_aware
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value,F
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
from leasing.models import Lease,Contract

def fetch_trial_balances_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "accounting","sql","mizan.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        TrialBalance.objects.select_related().all().delete()

        trial_balances = TrialBalance.objects.select_related("company","currency","partner").filter(company__id=int(company))
        partners = Partner.objects.select_related().filter(company__id=int(company))
        contracts = Contract.objects.select_related().filter(company__id=int(company))
        currencies = Currency.objects.select_related().all()
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        trial_balance_by_code = {t.account_id: t for t in trial_balances if t.account_id}
        partners_dict = {p.crm_code: p for p in partners}
        contracts_dict = {c.contract_id: c for c in contracts}
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
                    obj.main_account_code = str(data.AccountCode).split(".")[0] or ""
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
                    obj.contract = contracts_dict.get(str(data.ContractId))
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(TrialBalance(
                        company = company_obj,
                        account_id = str(data.AccountId) or "",
                        main_account_code = str(data.AccountCode).split(".")[0] or "",
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
                        total_credit_alternate = safe_decimal(data.TotalCreditAlternate),
                        contract = contracts_dict.get(str(data.ContractId))
                    ))
                    create_progress += 1
            if update_objs:
                TrialBalance.objects.bulk_update(update_objs, [
                    "account_id","main_account_code","account_code","account_code_trim","account_name","partner",
                    "balance_account_type","currency","balance_debit","balance_credit",
                    "total_debit","total_credit","balance_debit_alternate","balance_credit_alternate",
                    "total_debit_alternate","total_credit_alternate","contract"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                TrialBalance.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} mizan güncellendi.")
        print(f"Toplam {create_progress} mizan oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)

def fetch_trial_balance_transactions_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "accounting","sql","mizan_hareketleri.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            account_codes = [r.AccountCode for r in records]
            transaction_ids = [r.TransactionId for r in records]
            # trial_balances = TrialBalance.objects.filter(account_code__in=account_codes).only("account_code")
            trial_balances = TrialBalance.objects.filter(account_code__in=account_codes)
            #trial_balance_transactions = TrialBalanceTransaction.objects.filter(transaction_id__in=transaction_ids).only("transaction_id")
            trial_balance_transactions = TrialBalanceTransaction.objects.filter(transaction_id__in=transaction_ids)
            trial_balances_dict = {t.account_code: t for t in trial_balances}
            trial_balance_transactions_dict = {tt.transaction_id: tt for tt in trial_balance_transactions}
            for index,data in enumerate(records):
                if str(data.TransactionId):
                    obj = (trial_balance_transactions_dict.get(str(data.TransactionId)))
                else:
                    obj = None

                if obj:
                    obj.transaction_id = str(data.TransactionId) or ""
                    obj.trial_balance = trial_balances_dict.get(str(data.AccountCode)) or None
                    obj.ledger_period = str(data.LedgerPeriod) or ""
                    obj.transaction_text = str(data.TransactionText) or ""
                    obj.user_id = str(data.UserCodeCreated) or ""
                    obj.amount_type = str(data.AmountType) or ""
                    obj.local_amount = safe_decimal(data.AmountLocal)
                    obj.amount = safe_decimal(data.AmountCurrency)
                    obj.transaction_date = make_aware(data.TransactionDate) if data.TransactionDate else None
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(TrialBalanceTransaction(
                        company = company_obj,
                        transaction_id = str(data.TransactionId) or "",
                        trial_balance = trial_balances_dict.get(str(data.AccountCode)) or None,
                        ledger_period = str(data.LedgerPeriod) or "",
                        transaction_text = str(data.TransactionText) or "",
                        user_id = str(data.UserCodeCreated) or "",
                        amount_type = str(data.AmountType) or "",
                        local_amount = safe_decimal(data.AmountLocal),
                        amount = safe_decimal(data.AmountCurrency),
                        transaction_date = make_aware(data.TransactionDate) if data.TransactionDate else None
                    ))
                    create_progress += 1
            if update_objs:
                TrialBalanceTransaction.objects.bulk_update(update_objs, [
                    "transaction_id","trial_balance","ledger_period","transaction_text","user_id","amount_type","local_amount","amount","transaction_date"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                TrialBalanceTransaction.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} mizan hareketi güncellendi.")
        print(f"Toplam {create_progress} mizan hareketi oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)


def export_trial_balances(self):
    objs = Contract.objects.select_related().prefetch_related("contract_leases", "contract_trial_balances").filter(
        Q(contract_leases__is_last_project = True) &
        Q(contract_trial_balances__isnull=False) &
        ~Q(contract_leases__lease_status__in = ['baskasina_transfer_edildi'])
    ).distinct()

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()

    data = {
        "Transfer Kodu": [],
        "Sözleşme": [],
        "Hesap Kodu": [],
        "PB": [],
        "Borç Bakiyesi": [],
        "Alacak Bakiyesi": [],
        "Döviz Bakiye": [],
    }

    previous_progress = 0
    processed_leases = []
    transfer_code = 1
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        last_lease = obj.contract_leases.filter(is_last_project = True).first()

        leases = Lease.objects.select_related("contract").prefetch_related("contract__contract_trial_balances").filter(
            main_lease_id=last_lease.main_lease_id
        ).order_by('-lease_id')
        if leases:
            for lease in leases:
                if not lease.lease_id in processed_leases:
                    trial_balances = lease.contract.contract_trial_balances.select_related("currency","contract").all().distinct()
                    if trial_balances:
                        for trial_balance in trial_balances:
                            data["Transfer Kodu"].append(transfer_code)
                            data["Sözleşme"].append(trial_balance.contract.code or "")
                            data["Hesap Kodu"].append(trial_balance.account_code or "")
                            data["PB"].append(trial_balance.currency.code or "")
                            data["Borç Bakiyesi"].append(trial_balance.total_debit_alternate or Decimal("0.00"))
                            data["Alacak Bakiyesi"].append(trial_balance.total_credit_alternate or Decimal("0.00"))
                            data["Döviz Bakiye"].append(trial_balance.balance_debit_alternate - trial_balance.balance_credit_alternate or Decimal("0.00"))
            processed_leases.append(lease.lease_id)
            transfer_code += 1

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [
        "Borç Bakiyesi",
        "Alacak Bakiyesi",
        "Döviz Bakiye",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "accounting", "trial_balances", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-mizan.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sayfa', index=False)

        # Workbook'u al
        workbook = writer.book
        worksheet = writer.sheets['Sayfa']

        # Kolon isimlerine göre format uygula
        for idx, col in enumerate(df.columns, 1):  # enumerate 1'den başlıyor
            if col in numeric_columns:
                for cell in worksheet.iter_cols(min_col=idx, max_col=idx, min_row=2):
                    for c in cell:
                        c.number_format = '#,##0.00'   # İstediğin format
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()