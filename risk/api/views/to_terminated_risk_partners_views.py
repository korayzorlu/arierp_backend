from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,Exists,F,DateField,Sum
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

from leasing.models import Installment
from leasing.api.filters import LeaseFilter
from leasing.api.serializers import LeaseListSerializer
from core.permissions import SubscriptionPermission,BlockBrowserAccessPermission,RequireCustomHeaderPermission
from leasing.utils.common_utils import vendor_filter_for_views,project_filter_for_views


from risk.api.serializers.to_terminated_risk_partners_serializers import *
from risk.api.serializers import *
from risk.api.filters import *

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
    
class ToTerminatedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = ToTerminatedRiskPartnerListSerializer
    filterset_class = ToTerminatedRiskPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['max_overdue_days','total_overdue_amount','name','tc_vkn_no','crm_code']
    ordering = ['-max_overdue_days']
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
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = []
        prefetch_related_fields = ["partner_contracts__contract_leases", "partner_contracts__vendor"]

        #after_60_days = datetime.today() + timedelta(days=60)
        #after_30_days = datetime.today() + timedelta(days=30)

        # queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
        #     Q(company = active_company.company if active_company else None) &
        #     vendor_filter_for_views(self.request.query_params) &
        #     (
        #         Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
        #         Q(partner_contracts__contract_leases__lease_status='planlandi') |
        #         Q(partner_contracts__contract_leases__lease_status='durduruldu')
        #     ) &
        #     (
        #         Q(partner_contracts__contract_warning_notices__state='Yeni') |
        #         Q(partner_contracts__contract_warning_notices__state='Geçerli')
        #     ) &
        #     Q(partner_contracts__contract_leases__is_last_project=True) &
        #     Q(partner_contracts__contract_leases__is_kdv_diff=False) &
        #     Q(partner_contracts__contract_leases__is_credit=False) &
        #     Q(partner_contracts__contract_leases__is_under_review=False) &
        #     Q(partner_contracts__contract_warning_notices__service_date__isnull=False) &
        #     (
        #         Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=now().date()) |
        #         Q(partner_contracts__contract_comprehensive_warning_notices__official_cancellation_date__lte=now().date())
        #     ) &
        #     Q(partner_contracts__contract_leases__overdue_days__gt=25) &
        #     Q(partner_contracts__contract_leases__overdue_amount__gt=1000)
            
        #     #Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=now().date()) &
            
        # ).annotate(
        #     max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
        #     total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        #     # warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
        #     # comprehensive_warning_notice_count=Count('partner_contracts__contract_comprehensive_warning_notices', distinct=True),
        #     official_cancellation_date=Max(
        #         Case(
        #             When(
        #                 Q(partner_contracts__contract_warning_notices__state__in=['Yeni', 'Geçerli']) &
        #                 Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=now().date()),
        #                 then=F('partner_contracts__contract_warning_notices__official_cancellation_date')
        #             ),
        #             default=None,
        #             output_field=DateField()
        #         )
        #     ),
        #     # overdue_check=Case(
        #     #     When(
        #     #         customer_type='individual',
        #     #         then=Case(
        #     #             When(partner_contracts__contract_leases__overdue_days__gt=60, then=Value(True)),
        #     #             default=Value(False),
        #     #             output_field=BooleanField()
        #     #         )
        #     #     ),
        #     #     When(
        #     #         customer_type='institutional',
        #     #         then=Case(
        #     #             When(partner_contracts__contract_leases__overdue_days__gt=90, then=Value(True)),
        #     #             default=Value(False),
        #     #             output_field=BooleanField()
        #     #         )
        #     #     ),
        #     #     default=Value(False),
        #     #     output_field=BooleanField()
        #     # )
        # ).filter(official_cancellation_date__lte=now().date()).exclude(types__contains=["special"])

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            Q(partner_contracts__contract_leases__risk_status='fesih_edilecek')
            
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
        ).exclude(types__contains=["special"])

        #filter(warning_notice_count__gt=0,overdue_check=True).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
