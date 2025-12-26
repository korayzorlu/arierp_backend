from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,F,ExpressionWrapper,DecimalField
from django.db.models.functions import Lower,Upper
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.utils.timezone import now,localtime
from django.conf import settings
from django.utils.dateparse import parse_datetime


from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter
from rest_framework.response import Response
from rest_framework_datatables_editor.viewsets import DatatablesEditorModelViewSet, EditorModelMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

import traceback
from datetime import datetime,timedelta
import logging
import locale
import traceback

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission

from .serializers import *
from .filters import *
from finance.utils import get_finmaks_bank_accounts,get_finmaks_transactions
from common.utils.common_utils import normalize,safe_decimal
from common.models import ExchangeRate



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
    
class BankAccountList(ModelViewSet, QueryListAPIView):
    serializer_class = BankAccountListSerializer
    filterset_class = BankAccountFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    # pagination_class = DatatablesPagination
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
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering') or "bank_name"
        
        custom_related_fields = ["company"]

        queryset = FinmaksBankAccount.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        ).order_by(str(ordering))

        query = self.request.query_params.get('search[value]', None)
        if query:
            # Modelin tüm alanlarını otomatik olarak ekle, ForeignKey alanları hariç
            search_fields = [
                field.name for field in queryset.model._meta.get_fields()
                if not (field.is_relation and field.many_to_one)
            ]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset

class BankAccountBalanceList(ModelViewSet, QueryListAPIView):
    serializer_class = BankAccountListSerializer
    filterset_class = BankAccountFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    # pagination_class = DatatablesPagination
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
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        
        custom_related_fields = ["company"]

        queryset = FinmaksBankAccount.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        )

        if self.request.query_params.get('date'):
            date = self.request.query_params.get('date')
        else:
            date = localtime().date()

        usd_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="USD",date=date).first().forex_buying
        eur_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="EUR",date=date).first().forex_buying

        result = {
            'active_balances' : {
                'try_balance': queryset.filter(currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
                'usd_balance': queryset.filter(currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
                'usd_try_balance': (queryset.filter(currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * usd_exchange_rate,
                'eur_balance': queryset.filter(currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
                'eur_try_balance': (queryset.filter(currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * eur_exchange_rate,
                'total_try_balance': (queryset.filter(currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) + ((queryset.filter(currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * usd_exchange_rate) + ((queryset.filter(currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * eur_exchange_rate),
            },
            'bank_accounts' : {
                'yapi_kredi': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0067', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance': queryset.filter(bank_code='0067', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')
                    }],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0067', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0067', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')
                    }],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0067', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0067', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'albaraka': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0203', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0203', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0203', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0203', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0203', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0203', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'vakifbank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0015', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0015', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0015', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0015', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0015', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0015', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'vakif_katilim': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0210', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0210', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0210', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0210', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0210', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0210', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'akbank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0046', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0046', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0046', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0046', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0046', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0046', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'is_bank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0064', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0064', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'garanti': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='9999', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='9999', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='9999', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='9999', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='9999', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='9999', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'halkbank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0012', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0012', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0012', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0012', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0012', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0012', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'ziraat': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0010', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0010', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0010', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0010', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0010', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0010', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'ziraat_katilim': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0209', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0209', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0209', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0209', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0209', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0209', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'turkiye_finans': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0206', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0206', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0206', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0206', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0206', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0206', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'teb': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='8888', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='8888', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'kuveytturk': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='0205', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0205', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'emlak_katilim': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='7777', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='7777', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='7777', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='7777', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.account_no}",
                        # 'iban': obj.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(bank_code='7777', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='7777', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
            },
            'exchange_rates' : {
                'usd_exchange_rate': usd_exchange_rate,
                'eur_exchange_rate': eur_exchange_rate,
            }
        }

        return Response(result)
    
class BankAccountDailyRecordList(ModelViewSet, QueryListAPIView):
    serializer_class = BankAccountListSerializer
    filterset_class = BankAccountFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    # pagination_class = DatatablesPagination
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
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        
        custom_related_fields = ["company"]

        queryset = FinmaksBankAccountDailyRecord.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        )

        if self.request.query_params.get('date'):
            date = self.request.query_params.get('date')
        else:
            date = localtime().date()

        usd_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="USD",date=date).first().forex_buying
        eur_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="EUR",date=date).first().forex_buying

        result = {
            'active_balances' : {
                'try_balance': queryset.filter(finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
                'usd_balance': queryset.filter(finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
                'usd_try_balance': (queryset.filter(finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * usd_exchange_rate,
                'eur_balance': queryset.filter(finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
                'eur_try_balance': (queryset.filter(finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * eur_exchange_rate,
                'total_try_balance': (queryset.filter(finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) + ((queryset.filter(finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * usd_exchange_rate) + ((queryset.filter(finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * eur_exchange_rate),
            },
            'bank_accounts' : {
                'yapi_kredi': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0067', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance': queryset.filter(finmaks_bank_account__bank_code='0067', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0067', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0067', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0067', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0067', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'albaraka': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0203', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0203', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0203', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0203', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0203', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0203', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'vakifbank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0015', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0015', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0015', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0015', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0015', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0015', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'vakif_katilim': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0210', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0210', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0210', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0210', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0210', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0210', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'akbank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0046', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0046', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0046', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0046', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0046', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0046', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'is_bank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0064', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0064', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'garanti': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='9999', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='9999', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='9999', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='9999', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='9999', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='9999', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'halkbank': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0012', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0012', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0012', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0012', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0012', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0012', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'ziraat': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0010', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0010', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0010', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0010', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0010', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0010', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'ziraat_katilim': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0209', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0209', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0209', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0209', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0209', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0209', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'turkiye_finans': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0206', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0206', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0206', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0206', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0206', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0206', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'teb': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='8888', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='8888', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'kuveytturk': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='0205', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='0205', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
                'emlak_katilim': {
                    'try' : [{
                        'id':obj.id,
                        'account_no':  f"TRY - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='7777', finmaks_bank_account__currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='7777', finmaks_bank_account__currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'usd' : [{
                        'id':obj.id,
                        'account_no':  f"USD - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='7777', finmaks_bank_account__currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='7777', finmaks_bank_account__currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                    'eur' : [{
                        'id':obj.id,
                        'account_no':  f"EUR - {obj.finmaks_bank_account.account_no}",
                        # 'iban': obj.finmaks_bank_account.iban,
                        'balance': obj.available_balance} for obj in queryset.filter(finmaks_bank_account__bank_code='7777', finmaks_bank_account__currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(finmaks_bank_account__bank_code='7777', finmaks_bank_account__currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                },
            },
            'exchange_rates' : {
                'usd_exchange_rate': usd_exchange_rate,
                'eur_exchange_rate': eur_exchange_rate,
            }
        }

        return Response(result)

class BankAccountTransactionList(ModelViewSet, QueryListAPIView):
    serializer_class = BankAccountTransactionListSerializer
    filterset_class = BankAccountTransactionFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['transaction_date','transaction_id','explanation_field']
    ordering = ['-transaction_date']
    # pagination_class = DatatablesPagination
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

    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering') or "-transaction_date"
        
        custom_related_fields = ["company"]

        queryset = FinmaksTransaction.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        ).order_by(str(ordering))

        query = self.request.query_params.get('search[value]', None)
        if query:
            # Modelin tüm alanlarını otomatik olarak ekle, ForeignKey alanları hariç
            search_fields = [
                field.name for field in queryset.model._meta.get_fields()
                if not (field.is_relation and field.many_to_one)
            ]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class PartnerAdvanceList(ModelViewSet, QueryListAPIView):
    serializer_class = PartnerAdvanceListSerializer
    filterset_class = PartnerAdvanceFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = [f.name for f in Partner._meta.get_fields() if hasattr(f, 'name')] + ['trial_balance_amount']
    ordering = ['name']
    # pagination_class = DatatablesPagination
    def get_pagination_class(self):
        paginate = self.request.query_params.get('paginate')
        if paginate == 'false':
            return None
        return DatatablesPagination

    @property
    def pagination_class(self):
        return self.get_pagination_class()
    required_subscription = "free"
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        active_company_uuid = self.request.query_params.get('ac')
        if user.is_authenticated:
            active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        else:
            active_company = UserCompany.objects.select_related().filter(uuid = '899bc2f0-17d9-4067-a2a2-231b92bb9e59').first()

        # Use prefetch_related for partner_contracts to reduce DB hits
        custom_related_fields = []
        prefetch_related_fields = []

        balance_diff = ExpressionWrapper(
            F('partner_trial_balances__balance_debit') - F('partner_trial_balances__balance_credit'),
            output_field=DecimalField()
        )

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            (
                Q(advance_amount__gt=0) |
                Q(advance_amount__lt=0)
            )
        ).annotate(
            trial_balance_amount=Sum(
                Case(
                    When(partner_trial_balances__account_code__startswith='392.99.2.00', then=balance_diff),
                    When(partner_trial_balances__account_code__startswith='393.99.2.01', then=balance_diff),
                    default=Value(Decimal('0.00')),
                    output_field=DecimalField()
                )
            )
            # trial_balance_amount=Sum(F('partner_trial_balances__balance_debit') - F('partner_trial_balances__balance_credit')) or Decimal('0.00')
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["name","tc_vkn_no","crm_code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset