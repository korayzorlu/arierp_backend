from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,Exists, F
from django.db.models.functions import Lower,Upper,Coalesce
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.utils.timezone import now
from django.db.models.functions import TruncDate

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

from leasing.models import Installment
from leasing.api.filters import LeaseFilter
from leasing.api.serializers import LeaseListSerializer
from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission
from leasing.utils.common_utils import vendor_filter_for_views,project_filter_for_views


from risk.api.serializers.exchanged_leases_serializers import *
from risk.api.serializers import *
from risk.api.filters import *
from risk.utils.exchanged_leases_utils import compute_exchanged_amounts

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
    
class ExchangedLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = ExchangedLeaseListSerializer
    filterset_class = ExchangedLeaseFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['code','activation_date','lease_status','currency__code','project_no','status__name','leasing_type','application_no','current_request',
                       'finansman_kurum','bbsn','lease_status_update_date','kur_kaybi']
    ordering = ['-kur_kaybi']
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
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')

        # Bugünkü USD kurunu al
        today_usd_rate = ExchangeRate.objects.filter(
            date=date.today(), 
            target_currency__code="USD"
        ).first()
        today_forex = today_usd_rate.forex_buying if today_usd_rate else Decimal('1.00')
        
        custom_related_fields = ["company","contract","currency","status","contract__quotation_obj","contract__quotation_obj__quick_quotation"]

        # Installment toplamı
        installment_subquery = Installment.objects.select_related().filter(
            lease=OuterRef('pk'),
            payment_date__lte=date.today()
        ).values('lease').annotate(
            total=Sum('amount')
        ).values('total')[:1]
        
        # Trade transaction toplamı
        trade_subquery = TradeTransaction.objects.select_related().filter(
            lease=OuterRef('pk'),
            posting_group_name='Kira',
            amount_type='0',
            due_date__lte=datetime.now()
        ).values('lease').annotate(
            total=Sum('amount')
        ).values('total')[:1]

        queryset = Lease.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_serializers(self.request.query_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=0) &
            Q(overdue_amount__gt=100) &
            Q(is_last_project=True) &
            Q(is_tufe=False) &
            Q(currency__code__in=['TRY'])
        )

        queryset = queryset.annotate(
            installment_total=Coalesce(Subquery(installment_subquery), Decimal('0.00')),
            trade_total=Coalesce(Subquery(trade_subquery), Decimal('0.00')),
            # Yaklaşık kur kaybı (gerçek hesaplama tarihsel kur gerektirir)
            kur_kaybi=F('installment_total') / Value(today_forex) - F('trade_total') / Value(today_forex) - F('overdue_amount') / Value(today_forex)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code","contract__partner__name","contract__project","type","activation_date","lease_status","currency__code","project_no","status__name","leasing_type","application_no","current_request","finansman_kurum","bbsn"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset

        return queryset




