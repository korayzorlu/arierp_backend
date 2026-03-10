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
    
class ContractInSupplierList(ModelViewSet, QueryListAPIView):
    serializer_class = ContractInSupplierListSerializer
    filterset_class = ContractInSupplierFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company"]

        queryset = Contract.objects.select_related(*custom_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            Q(operation_status="tedarikcide")
        ).order_by("partner__name")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["code","partner__name","kof","quotation","committe","credit_type","customer_representative","supplier","project","status__name","mkk_tesciline_gonderilecek_mi","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class ContractInProcessList(ModelViewSet, QueryListAPIView):
    serializer_class = ContractInProcessListSerializer
    filterset_class = ContractInProcessFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company"]

        queryset = Contract.objects.select_related(*custom_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            Q(operation_status="islemde")
        ).order_by("partner__name")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["code","partner__name","kof","quotation","committe","credit_type","customer_representative","supplier","project","status__name","mkk_tesciline_gonderilecek_mi","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class ContractInArchiveList(ModelViewSet, QueryListAPIView):
    serializer_class = ContractInArchiveListSerializer
    filterset_class = ContractInArchiveFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company"]

        queryset = Contract.objects.select_related(*custom_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            Q(operation_status="arsivde")
        ).order_by("partner__name")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["code","partner__name","kof","quotation","committe","credit_type","customer_representative","supplier","project","status__name","mkk_tesciline_gonderilecek_mi","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class PartnerAdvanceActivityList(ModelViewSet, QueryListAPIView):
    serializer_class = PartnerAdvanceActivityListSerializer
    filterset_class = PartnerAdvanceActivityFilter
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
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["currency"]

        today = date.today()

        queryset = PartnerAdvanceActivity.objects.select_related(*custom_related_fields).filter(
            company = active_company.company if active_company else None
        ).order_by("created_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["currency__code","bank","bank_account_no","process_date","process_type","receipt_no","description"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class PartnerAdvanceActivityLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = PartnerAdvanceActivityLeaseListSerializer
    filterset_class = PartnerAdvanceActivityLeaseFilter
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
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["partner_advance_activity_activity","lease","lease__contract","lease__contract__quotation_obj","lease__contract__quotation_obj__quick_quotation"]

        queryset = PartnerAdvanceActivityLease.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            (
                Q(lease__lease_status='aktiflestirildi') |
                Q(lease__lease_status='planlandi') |
                Q(lease__lease_status='durduruldu')
            )
        ).order_by("-partner_advance_activity_activity__process_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["partner_advance_activity_activity__uuid","lease__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class TitleDeedInvoiceControlList(ModelViewSet, QueryListAPIView):
    serializer_class = TitleDeedInvoiceControlListSerializer
    filterset_class = TitleDeedInvoiceControlFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['code','activation_date','lease_status','currency__code','project_no','status__name','leasing_type','application_no','current_request','finansman_kurum','bbsn']
    ordering = ['-activation_date']
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
        
        custom_related_fields = ["company","contract","currency","status","contract__quotation_obj","contract__quotation_obj__quick_quotation"]

        queryset = Lease.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(is_last_project_arinet=True)
        ).exclude(
            Q(contract__partner__types__contains=['special'])
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