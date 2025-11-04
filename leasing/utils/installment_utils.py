from django.conf import settings

import pyodbc
import os
import pandas as pd
import io
import pyodbc
from decimal import Decimal
from datetime import datetime,date
from collections import defaultdict
import traceback

from leasing.models import *
from leasing.utils.common_utils import get_lease_status_value
from users.models import User
from leasing.models import *
from leasing.sqls import OVERDUE_INSTALLMENTS
from common.models import Currency
from common.utils.common_utils import normalize,safe_decimal,has_more_than_two_decimal_places
from partners.models import Partner

def fetch_installments_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "leasing","sql","taksitler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        # Installment.objects.select_related().filter(sequency = 0).delete()

        installments = Installment.objects.select_related("lease").filter(company__id=int(company))
        leases = Lease.objects.select_related().filter(company__id=int(company))
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id}
        leases_dict = {l.lease_id: l for l in leases}

        # installments_zeros = Installment.objects.select_related().filter(sequency = 0)
        # installments_zeros.delete()

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []
            for index,data in enumerate(records):
                if str(data.OperationProjectId):
                    obj = (installment_by_code.get((str(data.OperationProjectId),int(data.SequenceNo))))
                else:
                    obj = None

                if obj:
                    obj.lease = leases_dict.get(str(data.OperationProjectId))
                    obj.payment_date = data.PaymentDate.date() if data.PaymentDate else None
                    obj.vat = safe_decimal(data.VATRate)
                    obj.vat_amount = safe_decimal(data.VATAmount)
                    obj.payment = safe_decimal(data.Payment)
                    obj.amount = safe_decimal(data.TotalPaymentAmount)
                    # obj.principal = safe_decimal(data.PrincipalDisplay)
                    # obj.balance = safe_decimal(data.Balance)
                    # obj.interest = safe_decimal(data.InterestDisplay)
                    obj.sequency = int(data.SequenceNo)
                    obj.type = str(data.PaymentTypeId) or "1"
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Installment(
                        company = company_obj,
                        lease = leases_dict.get(str(data.OperationProjectId)),
                        payment_date = data.PaymentDate.date() if data.PaymentDate else None,
                        vat = safe_decimal(data.VATRate),
                        vat_amount = safe_decimal(data.VATAmount),
                        payment = safe_decimal(data.Payment),
                        amount = safe_decimal(data.TotalPaymentAmount),
                        # principal = safe_decimal(data.PrincipalDisplay),
                        # balance = safe_decimal(data.Balance),
                        # interest = safe_decimal(data.InterestDisplay),
                        sequency = int(data.SequenceNo),
                        type = str(data.PaymentTypeId) or "1"
                    ))
                    create_progress += 1
            if update_objs:
                Installment.objects.bulk_update(update_objs, [
                    "lease",
                    "payment_date",
                    "vat",
                    "vat_amount",
                    "payment",
                    "amount",
                    "principal",
                    "balance",
                    "interest",
                    "sequency",
                    "type"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Installment.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)
        print(f"Toplam {update_progress} taksit güncellendi.")
        print(f"Toplam {create_progress} taksit oluşturuldu.")
        print("--------")

        # Bir lease_id için birden fazla sequency=0 olan kayıtları teke düşür
        duplicates = (
            Installment.objects
            .filter(sequency=0)
            .values('lease__lease_id')
            .annotate(count_id=models.Count('id'))
            .filter(count_id__gt=1)
        )
        for dup in duplicates:
            lease_id = dup['lease__lease_id']
            installments = Installment.objects.filter(sequency=0, lease__lease_id=lease_id).order_by('id')
            # İlk kaydı bırak, diğerlerini sil
            to_delete = installments[1:]
            if to_delete:
                Installment.objects.filter(id__in=[i.id for i in to_delete]).delete()

    except Exception as e:
        print(e)
        traceback.print_exc()