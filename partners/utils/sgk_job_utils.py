from django.conf import settings
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.core.mail import EmailMessage, send_mail

import pyodbc
import os
import traceback
import logging
from datetime import datetime
from decimal import Decimal

from common.utils.common_utils import normalize,safe_decimal
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from partners.models import *


def fetch_sgk_jobs_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "partners","sql","meslekler.sql")
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
            # 1. codes
            sgk_job_ids = [r.ID for r in records]
            # 2. querysets
            sgk_jobs = SgkJob.objects.select_related().filter(sgk_job_id__in=sgk_job_ids)
            # 3. dicts
            sgk_job_dict = {l.sgk_job_id: l for l in sgk_jobs}
            for index,data in enumerate(records):
                if str(data.ID):
                    obj = (sgk_job_dict.get(str(data.ID)))
                else:
                    obj = None

                if obj:
                    obj.sgk_job_id = str(data.ID) or ""
                    obj.sgk_job_code = str(data.SgkJobCode) or ""
                    obj.description = str(data.JOB_CODE_DESCRIPTION) or ""
                    obj.is_pep = True if str(data.PEP_LIST_COMBO) == "Evet" else False

                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(SgkJob(
                        company = company_obj,
                        sgk_job_id = str(data.ID) or "",
                        sgk_job_code = str(data.SgkJobCode) or "",
                        description = str(data.JOB_CODE_DESCRIPTION) or "",
                        is_pep = True if str(data.PEP_LIST_COMBO) == "Evet" else False,

                    ))
                    create_progress += 1
            if update_objs:
                SgkJob.objects.bulk_update(update_objs, [
                    "sgk_job_id",
                    "sgk_job_code",
                    "description",
                    "is_pep",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                SgkJob.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} meslek güncellendi.")
        print(f"Toplam {create_progress} meslek oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)
        print(traceback.format_exc())



