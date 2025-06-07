from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter
from rest_framework.response import Response
from rest_framework_datatables_editor.viewsets import DatatablesEditorModelViewSet, EditorModelMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

import os
import logging
import pyodbc
import json

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission

from .serializers import *

from dotenv import load_dotenv
load_dotenv()

class QueryListAPIView(generics.ListAPIView):
    def get_queryset(self):
        if self.request.GET.get('format', None) == 'datatables':
            self.filter_backends = (OrderingFilter, DatatablesFilterBackend, DjangoFilterBackend, SearchFilter)
            return super().get_queryset()
        queryset = self.queryset

        # check the start index is integer
        try:
            start = self.request.GET.get('start')
            start = int(start) if start else None
        # else make it None
        except ValueError:
            start = None

        # check the end index is integer
        try:
            end = self.request.GET.get('end')
            end = int(end) if end else None
        # else make it None
        except ValueError:
            end = None

        # skip filters and sorting if they are not exists in the model to ensure security
        accepted_filters = {}
        # loop fields of the model
        for field in queryset.model._meta.get_fields():
            # if field exists in request, accept it
            if field.name in dict(self.request.GET):
                accepted_filters[field.name] = dict(self.request.GET)[field.name]
            # if field exists in sorting parameter's value, accept it

        filters = {}

        for key, value in accepted_filters.items():
            if any(val in value for val in EMPTY_VALUES):
                if queryset.model._meta.get_field(key).null:
                    filters[key + '__isnull'] = True
                else:
                    filters[key + '__exact'] = ''
            else:
                filters[key + '__in'] = value
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all().filter(**filters)[start:end]
        return queryset

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            elif self.request.GET.get('format', None) == 'datatables':
                self._paginator = self.pagination_class()
            else:
                self._paginator = None
        return self._paginator

class CariHesapHareketleriList(EditorModelMixin, ModelViewSet, QueryListAPIView):
    serializer_class = CariHesapHareketleriListSerializer
    filter_backends = [OrderingFilter,DjangoFilterBackend,SearchFilter]
    #filter_backends = []
    filterset_fields = {
                        'cari': ['exact','in', 'isnull']
    }
    search_fields = ['cari']
    ordering_fields = '__all__'
    pagination_class = PageNumberPagination

    def get_queryset(self):
        database = self.request.query_params.get('database')
        SERVER = os.getenv("MIKRO_SERVER","")
        DATABASE = database
        USERNAME = os.getenv("MIKRO_USERNAME","")
        PASSWORD = os.getenv("MIKRO_PASSWORD","")
        
        connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
        logger = logging.getLogger("django")
        try:
            conn = pyodbc.connect(connectionString)
            
            SQL_QUERY = """
            SELECT TOP (1000) cha_create_date,cha_belge_tarih,cha_kod,cha_evrak_tip,cha_belge_no,cha_d_cins,cha_meblag,cha_aratoplam,cha_ft_iskonto1,cha_ft_iskonto2,cha_ft_iskonto3,
            cha_ft_iskonto4,cha_ft_iskonto5,cha_ft_iskonto6,cha_vergi1,cha_vergi2,cha_vergi3,cha_vergi4,cha_vergi5,cha_vergi6,cha_vergi7,cha_vergi8,
            cha_vergi9,cha_vergi10,cha_d_kur,cha_projekodu,cha_aciklama
            FROM CARI_HESAP_HAREKETLERI
            ORDER BY cha_create_date DESC;
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            # for r in records:
                
            #     row_to_list = [elem for elem in r]
            
            external_data = []
            
            id = 1
            
            #####Cari Getir#####
            try:
                DATABASE = database
                connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
                conn = pyodbc.connect(connectionString)
                SQL_QUERY_CARI = """
                SELECT cari_kod,cari_unvan1 FROM CARI_HESAPLAR;
                """
                cursor = conn.cursor()
                cursor.execute(SQL_QUERY_CARI)
                cariRecords = cursor.fetchall()
                cariDict = {}
                for cariRecord in cariRecords:
                    row_to_list_evrak_tip = [elem for elem in cariRecord]
                    cariDict[str(row_to_list_evrak_tip[0])] = row_to_list_evrak_tip[1]
            except Exception as e:
                logger.exception(e)
                cariDict = {}
            #####Cari Getir-end#####
            
            #####Evrak Tip Getir#####
            try:
                DATABASE = "MikroDB_V16"
                connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
                conn = pyodbc.connect(connectionString)
                SQL_QUERY_EVRAK_TIP = """
                SELECT yit_sub_id, yit_isim2 FROM YARDIMCI_ISIM_TABLOSU
                WHERE yit_language = 'T' AND yit_tip_no = 0;
                """
                cursor = conn.cursor()
                cursor.execute(SQL_QUERY_EVRAK_TIP)
                evrakTipRecords = cursor.fetchall()
                evrakTipDict = {}
                for evrakTipRecord in evrakTipRecords:
                    row_to_list_evrak_tip = [elem for elem in evrakTipRecord]
                    evrakTipDict[str(row_to_list_evrak_tip[0])] = row_to_list_evrak_tip[1]
            except Exception as e:
                logger.exception(e)
                evrakTipDict = {}
            #####Evrak Tip Getir-end#####
            
            #####Doviz Getir#####
            try:
                DATABASE = "MikroDB_V16"
                connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
                conn = pyodbc.connect(connectionString)
                SQL_QUERY_EVRAK_TIP = """
                SELECT Kur_No, Kur_sembol FROM KUR_ISIMLERI;
                """
                cursor = conn.cursor()
                cursor.execute(SQL_QUERY_EVRAK_TIP)
                dovizRecords = cursor.fetchall()
                dovizDict = {}
                for dovizRecord in dovizRecords:
                    row_to_list_doviz = [elem for elem in dovizRecord]
                    dovizDict[str(row_to_list_doviz[0])] = row_to_list_doviz[1]
            except Exception as e:
                logger.exception(e)
                dovizDict = {}
            #####Doviz Getir-end#####
            
            evrakTipJSON = open("mikro/fixtures/evrak_tip.json")
            evrakTip = json.load(evrakTipJSON)
            
            for r in records:
                row_to_list = [elem for elem in r]
                
                iskonto = sum([r.cha_ft_iskonto1,r.cha_ft_iskonto2,r.cha_ft_iskonto3,r.cha_ft_iskonto4,r.cha_ft_iskonto5,r.cha_ft_iskonto6])
                vergi = sum([r.cha_vergi1,r.cha_vergi2,r.cha_vergi3,r.cha_vergi4,r.cha_vergi5,r.cha_vergi6,r.cha_vergi7,r.cha_vergi8,r.cha_vergi9,r.cha_vergi10])
                
                external_data.append({
                    "id" : id,
                    "tarih" : r.cha_create_date.strftime("%d.%m.%Y %H:%M:%S"),
                    "belgeTarih" : r.cha_belge_tarih.strftime("%d.%m.%Y %H:%M:%S"),
                    "kod" : r.cha_kod,
                    "cari" : cariDict.get(str(r.cha_kod)),
                    "evrakTip" : evrakTipDict.get(str(r.cha_evrak_tip)),
                    "belgeNo" : r.cha_belge_no,
                    "aciklama" : r.cha_aciklama,
                    "doviz" : dovizDict.get(str(r.cha_d_cins)),
                    "meblag" : r.cha_meblag,
                    "araToplam" : r.cha_aratoplam,
                    "iskonto" : iskonto,
                    "vergi" : vergi,
                    "kur" : r.cha_d_kur,
                    "proje" : r.cha_projekodu,
                })
                
                id = id + 1
            return external_data
        except Exception as e:
            logger.exception(e)
            return []
        
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        query = request.query_params.get('search[value]', None)
        
        if query:
            queryset = [item for item in queryset if item['cari'] and query.lower() in item['cari'].lower()]
            #queryset = [item for item in queryset if query.lower() in item['cari'].lower()]

        
        
        data_format = request.query_params.get('format', None)
        
        if data_format == 'datatables':
            draw = int(request.GET.get('draw', 1))
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 200))

            filtered_data = queryset[start:start+length]
            
            data = {
                "draw": draw,
                "recordsTotal": len(queryset),
                "recordsFiltered": len(queryset),
                "data": filtered_data
            }
            
            return Response(data)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PersonellerList(EditorModelMixin, ModelViewSet, QueryListAPIView):
    serializer_class = PersonellerListSerializer
    filter_backends = [OrderingFilter,DjangoFilterBackend,SearchFilter]
    #filter_backends = []
    filterset_fields = {
                        'isim': ['exact','in', 'isnull']
    }
    search_fields = ['isim']
    ordering_fields = '__all__'
    pagination_class = PageNumberPagination

    def get_queryset(self):
        database = self.request.query_params.get('database')
        SERVER = os.getenv("MIKRO_SERVER","")
        DATABASE = database
        USERNAME = os.getenv("MIKRO_USERNAME","")
        PASSWORD = os.getenv("MIKRO_PASSWORD","")
        
        connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
        logger = logging.getLogger("django")
        try:
            conn = pyodbc.connect(connectionString)
            
            SQL_QUERY = """
            SELECT TOP (1000) per_lastup_date,per_adi,per_soyadi,per_soyadi,per_giris_tar,per_cikis_tar,per_cikis_neden,per_ucret,per_kod,per_meslek_kodu
            FROM PERSONELLER
            ORDER BY per_lastup_date DESC;
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            # for r in records:
                
            #     row_to_list = [elem for elem in r]
            
            external_data = []
            
            id = 1
            
            #####Doviz Getir#####
            try:
                DATABASE = "MikroDB_V16"
                connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
                conn = pyodbc.connect(connectionString)
                SQL_QUERY_EVRAK_TIP = """
                SELECT Kur_No, Kur_sembol FROM KUR_ISIMLERI;
                """
                cursor = conn.cursor()
                cursor.execute(SQL_QUERY_EVRAK_TIP)
                dovizRecords = cursor.fetchall()
                dovizDict = {}
                for dovizRecord in dovizRecords:
                    row_to_list_doviz = [elem for elem in dovizRecord]
                    dovizDict[str(row_to_list_doviz[0])] = row_to_list_doviz[1]
            except Exception as e:
                logger.exception(e)
                dovizDict = {}
            #####Doviz Getir-end#####
            
            for r in records:
                row_to_list = [elem for elem in r]

                external_data.append({
                    "id" : id,
                    "tarih" : r.per_lastup_date.strftime("%d.%m.%Y %H:%M:%S"),
                    "isim" : r.per_adi,
                    "soyisim" : r.per_soyadi,
                    "girisTarihi" : r.per_giris_tar.strftime("%d.%m.%Y %H:%M:%S"),
                    "cikisTarihi" : r.per_cikis_tar.strftime("%d.%m.%Y %H:%M:%S"),
                    "cikisNeden" : r.per_cikis_neden,
                    "doviz" : "",
                    "ucret" : r.per_ucret,
                    "ikramiye" : r.per_kod,
                    "meslekKodu" : r.per_meslek_kodu,
                })
                
                id = id + 1
            return external_data
        except Exception as e:
            logger.exception(e)
            return []
        
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        query = request.query_params.get('search[value]', None)
        
        if query:
            queryset = [item for item in queryset if item['cari'] and query.lower() in item['cari'].lower()]
            #queryset = [item for item in queryset if query.lower() in item['cari'].lower()]

        
        
        data_format = request.query_params.get('format', None)
        
        if data_format == 'datatables':
            draw = int(request.GET.get('draw', 1))
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 200))

            filtered_data = queryset[start:start+length]
            
            data = {
                "draw": draw,
                "recordsTotal": len(queryset),
                "recordsFiltered": len(queryset),
                "data": filtered_data
            }
            
            return Response(data)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PersonelTahakkuklariList(EditorModelMixin, ModelViewSet, QueryListAPIView):
    serializer_class = PersonelTahakkuklariListSerializer
    filter_backends = [OrderingFilter,DjangoFilterBackend,SearchFilter]
    #filter_backends = []
    filterset_fields = {
                        'netUcret': ['exact','in', 'isnull']
    }
    search_fields = ['netUcret']
    ordering_fields = '__all__'
    pagination_class = PageNumberPagination

    def get_queryset(self):
        database = self.request.query_params.get('database')
        SERVER = os.getenv("MIKRO_SERVER","")
        DATABASE = database
        USERNAME = os.getenv("MIKRO_USERNAME","")
        PASSWORD = os.getenv("MIKRO_PASSWORD","")
        
        connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
        logger = logging.getLogger("django")
        try:
            conn = pyodbc.connect(connectionString)
            
            SQL_QUERY = """
            SELECT TOP (1000) pt_lastup_date,pt_maliyil,pt_tah_ay,pt_brutucret,pt_pkod,pt_net
            FROM PERSONEL_TAHAKKUKLARI
            ORDER BY pt_lastup_date DESC;
            """

            cursor = conn.cursor()
            cursor.execute(SQL_QUERY)
            
            records = cursor.fetchall()
            # for r in records:
                
            #     row_to_list = [elem for elem in r]
            
            external_data = []
            
            id = 1
            
            #####Personel Getir#####
            try:
                DATABASE = database
                connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Provider=SQLNCLI11;Integrated Security=SSPI;Persist Security Info=False;Initial Catalog=MASTER;Data Source=VSRV2;TrustServerCertificate=yes;'
                conn = pyodbc.connect(connectionString)
                SQL_QUERY_EVRAK_TIP = """
                SELECT per_kod, per_adi,per_soyadi
                FROM PERSONELLER;
                """
                cursor = conn.cursor()
                cursor.execute(SQL_QUERY_EVRAK_TIP)
                personelRecords = cursor.fetchall()
                personelDict = {}
                for personelRecord in personelRecords:
                    row_to_list_personel = [elem for elem in personelRecord]
                    personelDict[str(row_to_list_personel[0])] = f"{row_to_list_personel[1]} {row_to_list_personel[2]}"
            except Exception as e:
                logger.exception(e)
                personelDict = {}
            #####Personel Getir-end#####
            
            for r in records:
                row_to_list = [elem for elem in r]

                external_data.append({
                    "id" : id,
                    "tarih" : r.pt_lastup_date.strftime("%d.%m.%Y %H:%M:%S"),
                    "personel" : personelDict.get(str(r.pt_pkod)),
                    "donem" : f"{r.pt_tah_ay}/{r.pt_maliyil}",
                    "brutUcret" : r.pt_brutucret,
                    "netUcret" : r.pt_net,
                })
                
                id = id + 1
            return external_data
        except Exception as e:
            logger.exception(e)
            return []
        
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        query = request.query_params.get('search[value]', None)
        
        if query:
            queryset = [item for item in queryset if item['cari'] and query.lower() in item['cari'].lower()]
            #queryset = [item for item in queryset if query.lower() in item['cari'].lower()]

        
        
        data_format = request.query_params.get('format', None)
        
        if data_format == 'datatables':
            draw = int(request.GET.get('draw', 1))
            start = int(request.GET.get('start', 0))
            length = int(request.GET.get('length', 200))

            filtered_data = queryset[start:start+length]
            
            data = {
                "draw": draw,
                "recordsTotal": len(queryset),
                "recordsFiltered": len(queryset),
                "data": filtered_data
            }
            
            return Response(data)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

