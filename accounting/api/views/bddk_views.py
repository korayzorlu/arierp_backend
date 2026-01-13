from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q, Sum
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
from rest_framework.pagination import LimitOffsetPagination

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission

from datetime import date

from ..serializers.trial_balances_serializers import *
from ..filters.trial_balances_filters import *
from django.db.models import F, ExpressionWrapper, DecimalField

class QueryListAPIView(generics.ListAPIView):
    def get_queryset(self):
        if self.request.GET.get('format', None) == 'datatables':
            self.filter_backends = (OrderingFilter, DatatablesFilterBackend, DjangoFilterBackend)
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

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class DatatablesPagination(LimitOffsetPagination):
    default_limit = 50
    limit_query_param = 'length'
    offset_query_param = 'start'

    def get_paginated_response(self, data):
        return Response({
            'draw': int(self.request.query_params.get('draw', 0)),
            'recordsTotal': self.count,
            'recordsFiltered': self.count,
            'data': data
        })
    
class BDDKHesaplarList(ModelViewSet, QueryListAPIView):
    serializer_class = TrialBalanceListSerializer
    filterset_class = TrialBalanceFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    ## pagination_class = DatatablesPagination
    def get_pagination_class(self):
        paginate = self.request.query_params.get('paginate')
        if paginate == 'false':
            return None
        return DatatablesPagination

    @property
    def pagination_class(self):
        return self.get_pagination_class()
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]

    def list(self, request):
        active_company_uuid = request.query_params.get('ac')
        active_company = request.user.user_companies.filter(uuid=active_company_uuid).first()

        objs = TrialBalance.objects.select_related().filter(
            Q(company=active_company.company if active_company else None)
        )

        account_codes = [
            '010.00.1.00', '030.02.0.00', '030.19.0.00', '032.02.0.00', '038.00.0.00', '038.01.0.00',
            '032.90.0.0001', '032.90.0.0002', '032.90.0.0003', '022', '023', '150.00', '150.02', '150.01',
            '154.02.1', '154.02.2', '154.02.3', '154.03.4', '151.00', '151.01', '151.98', '151.02.1',
            '155.02.1', '155.02.2', '155.02.3', '155.03.4', '226', '227', '228', '229', '278', '279',
            '170', '171', '176', '177', '180', '181', '222.99.2', '223.98', '223.99.1', '223.99.2',
            '222.01.3', '223.01.3', '240', '250', '252', '254', '256.00', '256.01', '256.02', '256.08','258','256.07','280.01','281.01','281.98','238',
            '260.01','260.04','280.00','260.00','260.03','262','280.99','281.00','281.99','342','343','352.00','360.00.1','361.00.1','360.09.1','390',
            '361.09.1','361.99','391','392','393','380','350.01','350.03','350.04','386','410','412','414.03.1','414.05.0','414.09.0','420.09.2','420.00',
            '448','440','442','5','6','7','8','924','925','934','998','935','978','979','982','983','548','582','549','583','704','705','622.00','623.00','622.09',
            '623.09','644.00','810','820.01','830','840','850','880','820.03.9.00','882','570','571','771','861','790','599','791','792','820.00','821.00',
            '820.03.0.00','820.05','820.02','896','794','780.09.001','820.03.1','698.99.0',
        ]

        result = []
        for idx, code in enumerate(account_codes, start=1):
            total = objs.filter(Q(account_code__startswith=code)).aggregate(total_sum=Sum(F('total_debit') - F('total_credit')))['total_sum'] or Decimal('0.00')
            result.append({
                'id': idx,
                'account_code': code,
                'total': total,
                'currency': 'TRY',
            })

        return Response(result)
    
class Bl222afList(ModelViewSet, QueryListAPIView):
    serializer_class = TrialBalanceListSerializer
    filterset_class = TrialBalanceFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    ## pagination_class = DatatablesPagination
    def get_pagination_class(self):
        paginate = self.request.query_params.get('paginate')
        if paginate == 'false':
            return None
        return DatatablesPagination

    @property
    def pagination_class(self):
        return self.get_pagination_class()
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]

    def list(self, request):
        active_company_uuid = request.query_params.get('ac')
        active_company = request.user.user_companies.filter(uuid=active_company_uuid).first()

        objs = TrialBalance.objects.select_related().filter(
            Q(company=active_company.company if active_company else None)
        )

        row_names = [
            {
                'title': {'text': 'AKTİF KALEMLER', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'I. NAKİT, NAKİT BENZERLERİ ve MERKEZ BANKASI', 'font_weight': 'bold'},
                'tps': ['010.00.1.00','022'],
                'yps': ['023'],
            },
            {
                'title': {'text': 'II. GERÇEĞE UYGUN DEĞER FARKI KÂR/ZARARA YANSITILAN FİNANSAL VARLIKLAR (Net)', 'font_weight': 'bold'},
                'tps': ['030.02.0.00','030.19.0.00','038.00.0.00'],
                'yps': [],
            },
            {
                'title': {'text': 'III. TÜREV FİNANSAL VARLIKLAR', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'IV. GERÇEĞE UYGUN DEĞER FARKI DİĞER KAPSAMLI GELİRE YANSITILAN FİNANSAL VARLIKLAR (Net)  ', 'font_weight': 'bold'},
                'tps': ['032.02.0.00','038.01.0.00','032.90.0.0001','032.90.0.0002','032.90.0.0003'],
                'yps': [],
            },
            {
                'title': {'text': 'V. İTFA EDİLMİŞ MALİYETİ İLE ÖLÇÜLEN FİNANSAL VARLIKLAR (Net)', 'font_weight': 'bold'},
                'tps': ['150.00','154.02.1','154.02.2','154.02.3','150.02','150.01','154.03.4','222.99.2','222.01.3','170','176','180'],
                'yps': ['151.00','151.02.1','155.02.1','155.02.2','155.02.3','151.01','151.98','155.03.4','223.98','223.99.1','223.99.2','223.01.3','171','177','181'],
            },
            {
                'title': {'text': '5.1 Faktoring Alacakları', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.1.1 İskontolu Faktoring Alacakları (Net)', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.1.2 Diğer Faktoring Alacakları', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.2 Tasarruf Finansman Alacakları', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.2.1 Tasarruf Fon Havuzundan ', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.2.2 Özkaynaklardan', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.3 Finansman Kredileri', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.3.1 Tüketici Kredileri', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.3.2 Kredi Kartları', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.3.3 Taksitli Ticari Krediler', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '5.4 Kiralama İşlemleri (Net)', 'font_weight': 'normal'},
                'tps': ['150.00','154.02.1','154.02.2','154.02.3','150.02','150.01','154.03.4'],
                'yps': ['151.00','151.02.1','155.02.1','155.02.2','155.02.3','151.01','151.98','155.03.4'],
            },
            {
                'title': {'text': '5.4.1 Finansal Kiralama Alacakları', 'font_weight': 'normal'},
                'tps': ['150.00','154.02.1','154.02.2','154.02.3'],
                'yps': ['151.00','151.02.1','155.02.1','155.02.2','155.02.3'],
            },
            {
                'title': {'text': '5.4.2 Faaliyet Kiralaması Alacakları', 'font_weight': 'normal'},
                'tps': ['150.02'],
                'yps': [],
            },
            {
                'title': {'text': '5.4.3 Kazanılmamış Gelirler (-)', 'font_weight': 'normal'},
                'tps': ['150.01','154.03.4'],
                'yps': ['151.01','151.98','155.03.4'],
            },
            {
                'title': {'text': '5.5 İtfa Edilmiş Maliyeti İle Ölçülen Diğer Finansal Varlıklar', 'font_weight': 'normal'},
                'tps': ['222.99.2','222.01.3'],
                'yps': ['223.98','223.99.1','223.99.2','223.01.3'],
            },
            {
                'title': {'text': '5.6 Takipteki Alacaklar', 'font_weight': 'normal'},
                'tps': ['170','176'],
                'yps': ['171','177'],
            },
            {
                'title': {'text': '5.7 Beklenen Zarar Karşılıkları/Özel Karşılıklar (-)', 'font_weight': 'normal'},
                'tps': ['180'],
                'yps': ['181'],
            },
            {
                'title': {'text': 'VI. ORTAKLIK YATIRIMLARI', 'font_weight': 'bold'},
                'tps': ['246'],
                'yps': [],
            },
            {
                'title': {'text': '6.1 İştirakler (Net)', 'font_weight': 'normal'},
                'tps': ['246'],
                'yps': [],
            },
            {
                'title': {'text': '6.2 Bağlı Ortaklıklar (Net)', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '6.3 Birlikte Kontrol Edilen Ortaklıklar (İş Ortaklıkları) (Net)  ', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'VII. MADDİ DURAN VARLIKLAR (Net) ', 'font_weight': 'bold'},
                'tps': ['250','252','254','256.00','256.01','256.02','256.08'],
                'yps': [],
            },
            {
                'title': {'text': 'VIII. MADDİ OLMAYAN DURAN VARLIKLAR (Net)', 'font_weight': 'bold'},
                'tps': ['258','256.07'],
                'yps': [],
            },
            {
                'title': {'text': 'IX. YATIRIM AMAÇLI GAYRİMENKULLER (Net)', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },-
            {
                'title': {'text': 'X. CARİ DÖNEM VERGİ VARLIĞI', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'XI. ERTELENMİŞ VERGİ VARLIĞ', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'XII. DİĞER AKTİFLER', 'font_weight': 'bold'},
                'tps': ['226','228','278','280.01','260.01','260.04','280.00','260.00','260.03','280.99'],
                'yps': ['227','229','279','281.98','281.00','281.99'],
            },
            {
                'title': {'text': 'ARA TOPLAM', 'font_weight': 'bold'},
                'tps': ['010.00.1.00','022','030.02.0.00','030.19.0.00','038.00.0.00','032.02.0.00','038.01.0.00','032.90.0.0001','032.90.0.0002','032.90.0.0003','150.00','154.02.1','154.02.2','154.02.3','150.02','150.01','154.03.4','222.99.2','222.01.3','170','176','180','246','250','252','254','256.00','256.01','256.02','256.08','258','256.07','226','228','278','280.01','260.01','260.04','280.00','260.00','260.03','280.99'],
                'yps': ['023','151.00','151.02.1','155.02.1','155.02.2','155.02.3','151.01','151.98','155.03.4','223.98','223.99.1','223.99.2','223.01.3','171','177','181','227','229','279','281.98','281.00','281.99'],
            },
            {
                'title': {'text': 'XIII. SATIŞ AMAÇLI ELDE TUTULAN VE DURDURULAN FAALİYETLERE İLİŞKİN VARLIKLAR (Net)', 'font_weight': 'bold'},
                'tps': ['238'],
                'yps': [],
            },
            {
                'title': {'text': '13.1 Satış Amaçlı ', 'font_weight': 'normal'},
                'tps': ['238'],
                'yps': [],
            },
            {
                'title': {'text': '13.2 Durdurulan Faaliyetlere İlişkin', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'PASİF KALEMLER', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'I. ALINAN KREDİLER', 'font_weight': 'bold'},
                'tps': ['342','360.00.1','361.00.1'],
                'yps': ['343'],
            },
            {
                'title': {'text': 'II. FAKTORİNG BORÇLARI', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'III. TASARRUF FON HAVUZUNDAN BORÇLAR', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'IV. KİRALAMA İŞLEMLERİNDEN BORÇLAR', 'font_weight': 'bold'},
                'tps': ['352.00'],
                'yps': [],
            },
            {
                'title': {'text': 'V. İHRAÇ EDİLEN MENKUL KIYMETLER (Net)', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'VI. GERÇEĞE UYGUN DEĞER FARKI KAR ZARARA YANSITILAN FİNANSAL YÜKÜMLÜLÜKLER', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'VII. TÜREV FİNANSAL YÜKÜMLÜLÜKLER', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': 'VIII. KARŞILIKLAR', 'font_weight': 'bold'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '8.1 Yeniden Yapılanma Karşılığı', 'font_weight': 'normal'},
                'tps': [],
                'yps': [],
            },
            {
                'title': {'text': '8.2 Çalışan Hakları Yükümlülüğü Karşılığı', 'font_weight': 'normal'},
                'tps': ['350.01','350.03'],
                'yps': [],
            },
        ]

        result = []
        for idx, row_name in enumerate(row_names, start=1):
            if row_name['title']['text'] == 'AKTİF KALEMLER' or row_name['title']['text'] == 'PASİF KALEMLER':
                sira_no = ''
                tp = ''
                yp = ''
                toplam = ''
                bos = True
            else:
                sira_no = idx - 1

                tp = Decimal('0.00')
                yp = Decimal('0.00')

                for t in row_name['tps']:
                    tp += objs.filter(Q(account_code__startswith=t)).aggregate(total_sum=Sum(F('total_debit') - F('total_credit')))['total_sum'] or Decimal('0.00')
                for y in row_name['yps']:
                    yp += objs.filter(Q(account_code__startswith=y)).aggregate(total_sum=Sum(F('total_debit') - F('total_credit')))['total_sum'] or Decimal('0.00')

                tp = tp / Decimal('1000.00')
                yp = yp / Decimal('1000.00')
                toplam = tp + yp
                bos = True if len(row_name['tps']) == 0 and len(row_name['yps']) == 0 else False
            result.append({
                'id': sira_no,
                'sira_no': sira_no,
                'sira_adi': row_name['title'],
                'tp': tp,
                'yp': yp,
                'toplam': toplam,
                'bos': bos,
            })

        return Response(result)