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
            records = fetch_amounts_and_debits_sql(cursor,obj)

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