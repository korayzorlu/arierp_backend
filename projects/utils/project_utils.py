from django.conf import settings

import pyodbc
import os

from projects.models import Project
from companies.models import Company
from partners.models import Partner
from common.utils.common_utils import safe_decimal

def fetch_projects_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "projects","sql","projeler.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        projects = Project.objects.select_related("company","partner").filter(company__id=int(company))
        partners = Partner.objects.select_related().filter(company__id=int(company))
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        project_by_code = {p.project_id: p for p in projects if p.project_id}
        partners_dict = {p.crm_code: p for p in partners}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []

            for index,data in enumerate(records):
                if str(data.PROJECT_ID):
                    obj = (project_by_code.get(str(data.PROJECT_ID)))
                else:
                    obj = None

                if obj:
                    obj.project_id = str(data.PROJECT_ID) or ""
                    obj.name = str(data.PROJECT_NAME) or ""
                    obj.partner = partners_dict.get(str(data.VENDOR_ID))
                    obj.comission_rate = safe_decimal(data.COMMISSION_RATE)
                    obj.term_diff_rate = safe_decimal(data.TERM_DIFF_RATE)
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Project(
                        company = company_obj,
                        project_id = str(data.PROJECT_ID) or "",
                        name = str(data.PROJECT_NAME) or "",
                        partner = partners_dict.get(str(data.VENDOR_ID)),
                        comission_rate = safe_decimal(data.COMMISSION_RATE),
                        term_diff_rate = safe_decimal(data.TERM_DIFF_RATE),
                    ))
                    create_progress += 1

            if update_objs:
                Project.objects.bulk_update(update_objs, [
                    "project_id",
                    "name",
                    "partner",
                    "comission_rate",
                    "term_diff_rate",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Project.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} proje güncellendi.")
        print(f"Toplam {create_progress} proje oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)