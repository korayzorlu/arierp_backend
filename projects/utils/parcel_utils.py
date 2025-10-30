from django.conf import settings

import pyodbc
import os

from projects.models import Project,Parcel
from companies.models import Company
from partners.models import Partner
from common.utils.common_utils import safe_decimal

def fetch_parcels_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "projects","sql","parseller.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        parcels = Parcel.objects.select_related("company","project").filter(company__id=int(company))
        projects = Project.objects.select_related().filter(company__id=int(company))
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        parcel_by_code = {p.parcel_id: p for p in parcels if p.parcel_id}
        projects_dict = {p.project_id: p for p in projects}

        update_progress = 0
        create_progress = 0
        while True:
            records = cursor.fetchmany(BATCH_SIZE)
            if not records:
                break
            update_objs = []
            create_objs = []

            for index,data in enumerate(records):
                if str(data.PARCEL_ID):
                    obj = (parcel_by_code.get(str(data.PARCEL_ID)))
                else:
                    obj = None

                if obj:
                    obj.parcel_id = str(data.PARCEL_ID) or ""
                    obj.no = str(data.PARCEL_NO) or ""
                    obj.project = projects_dict.get(str(data.PROJECT_ID))
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(Parcel(
                        company = company_obj,
                        parcel_id = str(data.PARCEL_ID) or "",
                        no = str(data.PARCEL_NO) or "",
                        project = projects_dict.get(str(data.PROJECT_ID)),
                    ))
                    create_progress += 1

            if update_objs:
                Parcel.objects.bulk_update(update_objs, [
                    "parcel_id",
                    "no",
                    "project",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                Parcel.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} parsel güncellendi.")
        print(f"Toplam {create_progress} parsel oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)