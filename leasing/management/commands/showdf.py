from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

        # excel_file = pd.ExcelFile("media/CreditReportAccordingToDueReportba9d44a5-5ff6-4653-b323-0cf372e793c9.xls")
        # sheet_name = excel_file.sheet_names[0]

        # file_data = pd.read_excel("media/CreditReportAccordingToDueReportba9d44a5-5ff6-4653-b323-0cf372e793c9.xls", sheet_name)
        # df = pd.DataFrame(file_data)

        # with open("media/CreditReportAccordingToDueReportba9d44a5-5ff6-4653-b323-0cf372e793c9.xls", "r", encoding="utf-8") as f:
        #     for i in range(20):
        #         print(f.readline())

        # tables = pd.read_html(io.StringIO(html_content))
        # df = tables[0]

        # print(df.columns.tolist())
        # print(df.head())
                
        #print(len(df.iterrows()))




        with open("media/CreditReportAccordingToDueReportba9d44a5-5ff6-4653-b323-0cf372e793c9.xls", "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        table = soup.find("table")
        header_row = table.find("tr", class_="headerStyle")  # başlık satırı class'ına göre
        headers = [td.get_text(strip=True) for td in header_row.find_all("td")]

        print(headers)
        
        print("done!")