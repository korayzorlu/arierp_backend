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

        df = pd.read_excel("media/KİRA PLANI 16.06.2025.xlsx")

        # # Parçaları oluştur
        # parca1 = df.iloc[:300000]
        # parca2 = df.iloc[300000:600000]
        # parca3 = df.iloc[600000:]

        # # Her parçayı ayrı dosya olarak kaydet
        # parca1.to_excel("kira_plain_1.xlsx", index=False)
        # parca2.to_excel("kira_plain_2.xlsx", index=False)
        # parca3.to_excel("kira_plain_3.xlsx", index=False)

        # Parçaları oluştur
        parca1 = df.iloc[:100000]
        parca2 = df.iloc[100000:200000]
        parca3 = df.iloc[200000:300000]
        parca4 = df.iloc[300000:400000]
        parca5 = df.iloc[400000:500000]
        parca6 = df.iloc[500000:600000]
        parca7 = df.iloc[600000:700000]
        parca8 = df.iloc[700000:]

        # Her parçayı ayrı dosya olarak kaydet
        parca1.to_excel("kira_plani_1.xlsx", index=False)
        parca2.to_excel("kira_plani_2.xlsx", index=False)
        parca3.to_excel("kira_plani_3.xlsx", index=False)
        parca4.to_excel("kira_plani_4.xlsx", index=False)
        parca5.to_excel("kira_plani_5.xlsx", index=False)
        parca6.to_excel("kira_plani_6.xlsx", index=False)
        parca7.to_excel("kira_plani_7.xlsx", index=False)
        parca8.to_excel("kira_plani_8.xlsx", index=False)


        
        print("done!")