from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from purchasing.models import *
from purchasing.tasks import fetch_purchase_documents

import pandas as pd
import json
import os
import oracledb

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")

        oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_23_26")
        
        conn = oracledb.connect(
            user="AALKAN",
            password="ALEV75",
            dsn="192.168.48.20:1521/PROD"
        )

        sorgu = """
            SELECT a.sozlesme_no,
                a.ari_sozlesme_no,
                a.musteri_adi,
                a.tc_vergi_no,
                a.araci_kurum alt_musteri,
                a.araci_kurum_tc_vergi_no alt_musteri_tc_vergi_no,
                a.proje_id,
                ifsapp.project_api.Get_Description(proje_id) proje_adi,
                a.stok_no,
                a.sozlesme_tarihi,
                a.birim_fiyat,
                a.kdv_orani,
                a.nakit_tahsilat,
                a.senetli_tahsilat,
                a.objstate durum,
                nvl(a.company, ifsapp.project_api.Get_Company(proje_id)) sirket_kodu,
                ifsapp.company_api.get_name(nvl(a.company,
                                                ifsapp.project_api.Get_Company(proje_id))) sirket_unvani,
                a.fatura_tarihi,
                a.fatura_no,
                a.fatura_tutari,
                a.fatura_kdv_tutari
            FROM ifsapp.sincrm_sozlesme a
        """

        df = pd.read_sql(sorgu, conn)
        print(df.head(20))

        conn.close()

        df.to_excel("sonuclar.xlsx", index=False)
        
        print("done!")