from django.conf import settings

import pyodbc
import os

from projects.models import Project,RealEstate
from companies.models import Company
from partners.models import Partner
from common.utils.common_utils import safe_decimal

def fetch_real_estates_from_leaseflex(company,BATCH_SIZE=1000):
    try:
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "projects","sql","tasinmazlar.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        real_estates = RealEstate.objects.select_related("company","project").filter(company__id=int(company))
        projects = Project.objects.select_related().filter(company__id=int(company))
        company_obj = Company.objects.select_related().filter(id=int(company)).first()

        real_estate_by_code = {r.real_estate_id: r for r in real_estates if r.real_estate_id}
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
                if str(data.FREE_PART_ID):
                    obj = (real_estate_by_code.get(str(data.FREE_PART_ID)))
                else:
                    obj = None

                if obj:
                    obj.real_estate_id = str(data.FREE_PART_ID) or ""
                    obj.parcel = str(data.PARCEL_NO) or ""
                    obj.block = str(data.BLOCK_NO) or ""
                    obj.unit = str(data.FREE_PART_NO) or ""
                    obj.project = projects_dict.get(str(data.PROJECT_ID))
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(RealEstate(
                        company = company_obj,
                        real_estate_id = str(data.FREE_PART_ID) or "",
                        parcel = str(data.PARCEL_NO) or "",
                        block = str(data.BLOCK_NO) or "",
                        unit = str(data.FREE_PART_NO) or "",
                        project = projects_dict.get(str(data.PROJECT_ID)),
                    ))
                    create_progress += 1

            if update_objs:
                RealEstate.objects.bulk_update(update_objs, [
                    "real_estate_id",
                    "parcel",
                    "block",
                    "unit",
                    "project",
                ], batch_size=BATCH_SIZE)
            if create_objs:
                RealEstate.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} taşınmaz güncellendi.")
        print(f"Toplam {create_progress} taşınmaz oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)