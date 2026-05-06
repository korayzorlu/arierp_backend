from django.conf import settings

import pyodbc
import os
import pandas as pd
from datetime import datetime

from projects.models import Project,RealEstate
from companies.models import Company
from partners.models import Partner
from common.utils.common_utils import safe_decimal
from projects.models import RealEstate

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
                    obj.real_estate_id = str(data.FREE_PART_ID) if data.FREE_PART_ID else None
                    obj.parcel = str(data.PARCEL_NO) if data.PARCEL_NO else None
                    obj.block = str(data.BLOCK_NO) if data.BLOCK_NO else None
                    obj.unit = str(data.FREE_PART_NO) if data.FREE_PART_NO else None
                    obj.project = projects_dict.get(str(data.PROJECT_ID)) if data.PROJECT_ID else None
                    obj.bbsn = str(data.BBSN_NO) if data.BBSN_NO else None
                    update_objs.append(obj)
                    update_progress += 1
                else:
                    create_objs.append(RealEstate(
                        company = company_obj,
                        real_estate_id = str(data.FREE_PART_ID) if data.FREE_PART_ID else None,
                        parcel = str(data.PARCEL_NO) if data.PARCEL_NO else None,
                        block = str(data.BLOCK_NO) if data.BLOCK_NO else None,
                        unit = str(data.FREE_PART_NO) if data.FREE_PART_NO else None,
                        project = projects_dict.get(str(data.PROJECT_ID)) if data.PROJECT_ID else None,
                        bbsn = str(data.BBSN_NO) if data.BBSN_NO else None
                    ))
                    create_progress += 1

            if update_objs:
                RealEstate.objects.bulk_update(update_objs, [
                    "real_estate_id",
                    "parcel",
                    "block",
                    "unit",
                    "project",
                    "bbsn"
                ], batch_size=BATCH_SIZE)
            if create_objs:
                RealEstate.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

        print(f"Toplam {update_progress} taşınmaz güncellendi.")
        print(f"Toplam {create_progress} taşınmaz oluşturuldu.")
        print("--------")
    except Exception as e:
        print(e)

def export_real_estates(self):
    objs = RealEstate.objects.select_related("project").filter().order_by("project__name","block","unit")

    self.process.status = "in_progress"
    self.process.items_count = len(objs)
    self.process.save()
    
    data = {
        "Proje": [],
        "Proje ID": [],
        "Taşınmaz ID": [],
        "Blok": [],
        "Bağımsız Bölüm": [],
        "BBSN": [],
    }

    previous_progress = 0
    metin = ""
    for index,obj in enumerate(objs):
        current_progress = ((index + 1)/len(objs))*100

        if current_progress - previous_progress >= 5:
            self.process.progress = int(current_progress)
            self.process.save()
            previous_progress = current_progress

        data["Proje"].append(obj.project.name if obj.project else "")
        data["Proje ID"].append(obj.project.project_id if obj.project else "")
        data["Taşınmaz ID"].append(obj.real_estate_id)
        data["Blok"].append(obj.block)
        data["Bağımsız Bölüm"].append(obj.unit)
        data["BBSN"].append(obj.bbsn)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    numeric_columns = [

    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "projects", "real_estates", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-tasinmazlar.xlsx"
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


       