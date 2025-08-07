from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value
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
    
class LeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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
        
        custom_related_fields = ["company","contract","currency","status","contract__quotation_obj","contract__quotation_obj__quick_quotation"]

        if ordering:
            queryset = Lease.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by(str(ordering))
        else:
            queryset = Lease.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("-activation_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code","contract__partner__name","contract__project","type","activation_date","lease_status","currency__code","project_no","status__name","leasing_type","application_no","current_request","finansman_kurum","bbsn"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class LeaseUnpageList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company","contract","currency","status","contract__quotation_obj","contract__quotation_obj__quick_quotation"]

        if ordering:
            queryset = Lease.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by(str(ordering))
        else:
            queryset = Lease.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("-activation_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code","contract__partner__name","contract__project","type","activation_date","lease_status","currency__code","project_no","status__name","leasing_type","application_no","current_request","finansman_kurum","bbsn"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset
    
class InstallmentList(ModelViewSet, QueryListAPIView):
    serializer_class = InstallmentListSerializer
    filterset_class = InstallmentFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company","lease","lease__currency","lease__contract","lease__contract__partner","lease__contract__quotation_obj__quick_quotation"]

        queryset = Installment.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("lease__code","sequency")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["lease__code","sequency","lease__currency__code","lease__contract__code","lease__contract__partner__name"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class BankActivityList(ModelViewSet, QueryListAPIView):
    serializer_class = BankActivityListSerializer
    filterset_class = BankActivityFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    #pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["currency"]

        queryset = BankActivity.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("tc_vkn_no")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["currency__code","bank","bank_account_no","process_date","process_type","receipt_no","description"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class BankActivityLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = BankActivityLeaseListSerializer
    filterset_class = BankActivityLeaseFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    #pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["bank_activity","lease","lease__contract","lease__contract__quotation_obj","lease__contract__quotation_obj__quick_quotation"]

        queryset = BankActivityLease.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            (
                Q(lease__lease_status='aktiflestirildi') |
                Q(lease__lease_status='planlandi') |
                Q(lease__lease_status='durduruldu')
            )
        ).order_by("-bank_activity__process_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["bank_activity__uuid","lease__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class RiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = RiskPartnerListSerializer
    filterset_class = RiskPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        user = self.request.user
        active_company_uuid = self.request.query_params.get('active_company')
        if user.is_authenticated:
            active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        else:
            active_company = UserCompany.objects.select_related().filter(uuid = '899bc2f0-17d9-4067-a2a2-231b92bb9e59').first()
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]
        
        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=100) &
            Q(partner_contracts__contract_leases__overdue_days__lte=30) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class RiskPartnerKDVList(ModelViewSet, QueryListAPIView):
    serializer_class = RiskPartnerKDVListSerializer
    filterset_class = RiskPartnerKDVFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=100) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=True)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset


class ToWarnedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = ToWarnedRiskPartnerListSerializer
    filterset_class = ToWarnedRiskPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=1000) &
            Q(partner_contracts__contract_leases__overdue_days__gt=30) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count=0).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class WarnedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = WarnedRiskPartnerListSerializer
    filterset_class = WarnedRiskPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=1000) &
            Q(partner_contracts__contract_leases__overdue_days__gt=30) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    customer_type='individual',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__lte=60, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    customer_type='institutional',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__lte=90, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset


class ToTerminatedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = ToTerminatedRiskPartnerListSerializer
    filterset_class = ToTerminatedRiskPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]

        #after_60_days = datetime.today() + timedelta(days=60)
        #after_30_days = datetime.today() + timedelta(days=30)

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=1000) &
            Q(partner_contracts__contract_leases__overdue_days__gt=30) &
            Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=datetime.today() - timedelta(days=5)) &
            (
                Q(partner_contracts__contract_warning_notices__state='Yeni') |
                Q(partner_contracts__contract_warning_notices__state='Geçerli')
            ) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            #Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=now().date()) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) 
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    customer_type='individual',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__gt=65, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    customer_type='institutional',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__gt=95, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class DeliveryConfirmList(ModelViewSet, QueryListAPIView):
    serializer_class = DeliveryConfirmListSerializer
    filterset_class = DeliveryConfirmFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount=0) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) &
            Q(partner_contracts__contract_leases__paid_rate__gte=30) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            )
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        ).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
 
class TomorrowPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = TomorrowPartnerListSerializer
    filterset_class = TomorrowPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["country","billing_country"]

        tomorrow = date.today() + timedelta(days=1)

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__lease_installments__payment_date=tomorrow) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            )
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days')
        ).exclude(types__contains=["special"]).order_by('-max_overdue_days')

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class TodayPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = TodayPartnerListSerializer
    filterset_class = TodayPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["country","billing_country"]

        today = date.today()

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__lease_installments__payment_date=today) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            )
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days')
        ).exclude(types__contains=["special"]).order_by('-max_overdue_days')

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    



####out api
class OutRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = RiskPartnerListSerializer
    filterset_class = RiskPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
    #pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        user = self.request.user
        active_company_uuid = self.request.query_params.get('ac')
        if user.is_authenticated:
            active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        else:
            active_company = UserCompany.objects.select_related().filter(uuid = '899bc2f0-17d9-4067-a2a2-231b92bb9e59').first()

        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = ["country","billing_country"]

        distinct_authors = Contract.objects.values_list('project', flat=True).distinct()
        for distinct_author in distinct_authors:
            print(distinct_author)

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=100) &
            Q(partner_contracts__contract_leases__overdue_days__lte=30) &
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset