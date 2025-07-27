from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,F
from django.db.models.functions import Lower,Upper
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
    
class ContractList(ModelViewSet, QueryListAPIView):
    serializer_class = ContractListSerializer
    filterset_class = ContractFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","partner","status"]

        queryset = Contract.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("-kof_tan_sozlesmeye_aktarim_tarihi")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["code","partner__name","kof","quotation","committe","credit_type","customer_representative","supplier","project","status__name","mkk_tesciline_gonderilecek_mi","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class ContractPaymentList(ModelViewSet, QueryListAPIView):
    serializer_class = ContractPaymentListSerializer
    filterset_class = ContractPaymentFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","contract","currency"]

        queryset = ContractPayment.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("date","contract__code")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = [
                    "uuid",
                    "contract__code",
                    "trn_id",
                    "trn_from_id",
                    "coledger_account_idde",
                    "ledger_account_name",
                    "trade_account_code",
                    "type",
                    "posting_type",
                    "group_name",
                    "account_code",
                    "account_name",
                    "currency__code",
                    "user_name",
                    "description",
                ]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class WarningNoticeList(ModelViewSet, QueryListAPIView):
    serializer_class = WarningNoticeListSerializer
    filterset_class = WarningNoticeFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['contract_code','partner_name','process_start_date','service_date','official_cancellation_date','debit_amount','paid','diff']
    ordering = ['-official_cancellation_date']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","contract","contract__currency","contract__partner"]

        queryset = WarningNotice.objects.select_related(*custom_related_fields).filter(
            company = active_company.company if active_company else None
        ).annotate(
            contract_code=F('contract__code'),
            partner_name=F('contract__partner__name')
        ).order_by("-process_start_date","contract__code")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = [
                    "uuid",
                    "contract__code",
                    "document_id",
                    "risk_id",
                    "customer_id",
                    "daily_wages_date",
                    "process_start_date",
                    "service_date",
                    "official_cancellation_date",
                    "state",
                    "approval_state",
                    "contract__currency_code",
                ]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset