from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from django.db.models import Q

import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict

from .models import *
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal
from partners.models import Partner

@shared_task()
def fetch_purchase_payments(company):
    excel_file = pd.ExcelFile("files/satici-odemeleri.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/satici-odemeleri.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    purchase_payments = PurchasePayment.objects.select_related().all()
    purchase_payments.delete()

    purchase_payment_by_code = {l.lease.code: l for l in purchase_payments if l.lease.code}

    previous_progress = 0
    old_obj_count = 0
    new_obj_count = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        obj = (purchase_payment_by_code.get(str(row['Kira Planı Kodu'])))

        # obj = Lease.objects.select_related().filter(
        #     Q(code=str(row['Kira Planı'])) &
        #     (
        #         Q(lease_status='aktiflestirildi') |
        #         Q(lease_status='planlandi') |
        #         Q(lease_status='durduruldu')
        #     )
        # ).first()
        if obj:
            old_obj_count += 1
            obj.lease = Lease.objects.select_related().filter(code=str(row['Kira Planı Kodu'])).first()
            obj.total_contract_amount = Decimal(str(row['Toplam Sözleşme Bedeli (İlk Sözleşme)'])) if not pd.isna(row['Toplam Sözleşme Bedeli (İlk Sözleşme)']) else Decimal("0.00")
            obj.total_vendor_payment = Decimal(str(row['Satıcı Ödemeleri Toplam Tutarı'])) if not pd.isna(row['Satıcı Ödemeleri Toplam Tutarı']) else Decimal("0.00")
            obj.before_total_payment = Decimal(str(row['Ödeme Toplam Öncesi'])) if not pd.isna(row['Ödeme Toplam Öncesi']) else Decimal("0.00")
            obj.purchasing = int(row['satinalma']) if not pd.isna(row['satinalma']) else 0
            obj.save()
        else:
            new_obj_count += 1
            PurchasePayment.objects.create(
                company=Company.objects.get(id=company),
                lease=Lease.objects.select_related().filter(code=str(row['Kira Planı Kodu'])).first(),
                total_contract_amount=Decimal(str(row['Toplam Sözleşme Bedeli (İlk Sözleşme)'])) if not pd.isna(row['Toplam Sözleşme Bedeli (İlk Sözleşme)']) else Decimal("0.00"),
                total_vendor_payment=Decimal(str(row['Satıcı Ödemeleri Toplam Tutarı'])) if not pd.isna(row['Satıcı Ödemeleri Toplam Tutarı']) else Decimal("0.00"),
                before_total_payment=Decimal(str(row['Ödeme Toplam Öncesi'])) if not pd.isna(row['Ödeme Toplam Öncesi']) else Decimal("0.00"),
                purchasing=int(row['satinalma']) if not pd.isna(row['satinalma']) else 0
            )

    print(f"{new_obj_count} objects created and {old_obj_count} objects updated for leases.")
