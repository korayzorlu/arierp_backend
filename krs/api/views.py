from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,Exists,F
from django.db.models.functions import Lower,Upper
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
from dateutil.relativedelta import relativedelta

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission

from .serializers import *
from .filters import *

from risk.api.filters import RiskPartnerFilter
from risk.api.serializers.risk_partners_serializers import *
from leasing.utils.common_utils import vendor_filter_for_views,project_filter_for_views

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


class KapamaDetayList(ModelViewSet, QueryListAPIView):
    serializer_class = KapamaDetayListSerializer
    filterset_class = KapamaDetayFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date","contract_header_id","odeme_tarihi","fatura_tarihi","kapatilan_tutar"]
    ordering = ['-odeme_tarihi']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KapamaDetay.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract_header_id"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class KapamaHareketiList(ModelViewSet, QueryListAPIView):
    serializer_class = KapamaHareketiListSerializer
    filterset_class = KapamaHareketiFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date","contract_header_id","tarih","fatura_tutar","odeme_tutar","kapatilan_fatura_tutar","temerrut_tutar","bugune_kadar_temerrut","odenmis_temerrut","gercek_odeme_tutar","protokol","sentetik"]
    ordering = ['-tarih']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KapamaHareketi.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract_header_id"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset

class KrsReportList(ModelViewSet, QueryListAPIView):
    serializer_class = KrsReportListSerializer
    filterset_class = KrsReportFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    # ordering_fields = ["created_date"]
    # ordering = ['-created_date']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KrsReport.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        ).annotate(
            cs0000_first=Case(
                When(kayit_turu=KayitTuru.CS0000, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
            kayit_turu_sira=Case(
                When(kayit_turu=KayitTuru.CS0100, then=Value(0)),
                When(kayit_turu=KayitTuru.CS0200, then=Value(1)),
                When(kayit_turu=KayitTuru.CS0301, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
            cs9999_last=Case(
                When(kayit_turu=KayitTuru.CS9999, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by("cs0000_first", "hesap_numarasi", "kayit_turu_sira", "cs9999_last")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class KrsReportCS0000List(ModelViewSet, QueryListAPIView):
    serializer_class = KrsReportCS0000ListSerializer
    filterset_class = KrsReportFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date"]
    ordering = ['-created_date']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KrsReport.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(kayit_turu=KayitTuru.CS0000)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class KrsReportCS0100List(ModelViewSet, QueryListAPIView):
    serializer_class = KrsReportCS0100ListSerializer
    filterset_class = KrsReportFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date"]
    ordering = ['-created_date']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KrsReport.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(kayit_turu=KayitTuru.CS0100)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class KrsReportCS0200List(ModelViewSet, QueryListAPIView):
    serializer_class = KrsReportCS0200ListSerializer
    filterset_class = KrsReportFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date"]
    ordering = ['-created_date']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KrsReport.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(kayit_turu=KayitTuru.CS0200)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class KrsReportCS0301List(ModelViewSet, QueryListAPIView):
    serializer_class = KrsReportCS0301ListSerializer
    filterset_class = KrsReportFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date"]
    ordering = ['-created_date']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KrsReport.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(kayit_turu=KayitTuru.CS0301)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class KrsReportCS9999List(ModelViewSet, QueryListAPIView):
    serializer_class = KrsReportCS9999ListSerializer
    filterset_class = KrsReportFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ["created_date"]
    ordering = ['-created_date']
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = KrsReport.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(kayit_turu=KayitTuru.CS9999)
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset