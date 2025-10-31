from django.conf import settings

import pyodbc
import os
import pandas as pd
from decimal import Decimal

from projects.models import Project,RealEstate,TitleDeed
from companies.models import Company
from partners.models import Partner
from common.utils.common_utils import safe_decimal

def import_title_deeds_from_excel(company):
    excel_file = pd.ExcelFile("files/guncel-tapu.xlsx")
    sheet_name = excel_file.sheet_names[0]

    file_data = pd.read_excel("files/guncel-tapu.xlsx", sheet_name)
    df = pd.DataFrame(file_data)

    title_deeds = TitleDeed.objects.select_related().filter(company__id=int(company))
    company_obj = Company.objects.select_related().filter(id=int(company)).first()

    title_deed_by_code = {l.tasinmaz_no: l for l in title_deeds if l.tasinmaz_no}

    previous_progress = 0
    old_obj_count = 0
    for index,row in df.iterrows():
        current_progress = ((index + 1)/len(df))*100

        if current_progress - previous_progress >= 1:
            previous_progress = current_progress
            print(f"{int(current_progress)} %")

        obj = (title_deed_by_code.get(str(row['Taşınmaz No'])))

        if obj:
            old_obj_count += 1
            obj.tasinmaz_no = str(row['Taşınmaz No']) if not pd.isna(row['Taşınmaz No']) else ""
            obj.nitelik = str(row['Nitelik']) if not pd.isna(row['Nitelik']) else ""
            obj.il = str(row['İl']) if not pd.isna(row['İl']) else ""
            obj.ilce = str(row['İlçe']) if not pd.isna(row['İlçe']) else ""
            obj.mahalle = str(row['Mahalle']) if not pd.isna(row['Mahalle']) else ""
            obj.yuzolcum = Decimal(str(row['Yüzölçüm'])) if not pd.isna(row['Yüzölçüm']) else Decimal("0.00")
            obj.ada = str(int(row['Ada'])) if not pd.isna(row['Ada']) else ""
            obj.parsel = str(row['Parsel']) if not pd.isna(row['Parsel']) else ""
            obj.unit = str(row['Bağımsız Bölüm No']) if not pd.isna(row['Bağımsız Bölüm No']) else ""
            obj.zemin_hisse_id = str(row['Zemin Hisse ID']) if not pd.isna(row['Zemin Hisse ID']) else ""
            obj.zemin_tipi = str(row['Zemin_Tipi']) if not pd.isna(row['Zemin_Tipi']) else ""
            obj.save()
        else:
            obj = TitleDeed.objects.create(
                company = company_obj,
                tasinmaz_no = str(row['Taşınmaz No']) if not pd.isna(row['Taşınmaz No']) else "",
                nitelik = str(row['Nitelik']) if not pd.isna(row['Nitelik']) else "",
                il = str(row['İl']) if not pd.isna(row['İl']) else "",
                ilce = str(row['İlçe']) if not pd.isna(row['İlçe']) else "",
                mahalle = str(row['Mahalle']) if not pd.isna(row['Mahalle']) else "",
                yuzolcum = Decimal(str(row['Yüzölçüm'])) if not pd.isna(row['Yüzölçüm']) else Decimal("0.00"),
                ada = str(int(row['Ada'])) if not pd.isna(row['Ada']) else "",
                parsel = str(row['Parsel']) if not pd.isna(row['Parsel']) else "",
                unit = str(row['Bağımsız Bölüm No']) if not pd.isna(row['Bağımsız Bölüm No']) else "",
                zemin_hisse_id = str(row['Zemin Hisse ID']) if not pd.isna(row['Zemin Hisse ID']) else "",
                zemin_tipi = str(row['Zemin_Tipi']) if not pd.isna(row['Zemin_Tipi']) else "",
            )

    print(f"{old_obj_count} objects updated for title deed.")