from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,F,ExpressionWrapper,DecimalField
from django.db.models.functions import Lower,Upper
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.utils.timezone import now

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
import requests
import xmltodict
import json

from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission

from .serializers import *
from .filters import *

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
    
class PurchasePaymentList(ModelViewSet, QueryListAPIView):
    serializer_class = PurchasePaymentListSerializer
    filterset_class = PurchasePaymentFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['total_purchase_document','diff','total_contract_amount','total_vendor_payment','before_total_payment','after_total_payment',
                       'managing_expense','lease_payment_amount','vendor_payment_with_report_date','next_payment','purchasing']
    ordering = ['-diff']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company","lease__contract__partner"]

        # url = f"http://192.168.48.49/SinpasCrmService/crm.asmx/AriTahsilatGetir?SozlesmeNo=M-FST.0097&Tarih=2026-01-26"

        # response = requests.get(url)
        # data_dict = xmltodict.parse(response.text)
        # json_data = json.dumps(data_dict, ensure_ascii=False, indent=2)

        # result = data_dict["AriTahsilatSonucu"]

        # print(result['TahsilatTutari'])
        # print(type(result['TahsilatTutari']))

        queryset = PurchasePayment.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            ~Q(lease__contract__partner__types__contains=['special']) &
            ~Q(lease__contract__partner__crm_code__in=["23371", "9341", "10495", "4305", "10437", "4441", "11722", "24120"])
        ).annotate(
            total_purchase_document=Sum('lease__lease_purchase_documents__total_amount'),
            diff=ExpressionWrapper(
                F('lease_payment_amount') - F('before_total_payment'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        # .exclude(
        #     lease__contract__partner__crm_code__in=["23371", "9341", "10495", "4305", "10437", "4441", "11722", "24120"]
        # )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = []
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class PurchaseDocumentList(ModelViewSet, QueryListAPIView):
    serializer_class = PurchaseDocumentListSerializer
    filterset_class = PurchaseDocumentFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company"]

        queryset = PurchaseDocument.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        ).order_by("lease__contract__code")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = []
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset