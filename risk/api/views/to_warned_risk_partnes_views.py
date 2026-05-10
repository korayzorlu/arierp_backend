from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,F, ExpressionWrapper, DateField,IntegerField
from django.db.models.functions import Lower,Upper,Cast
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


from risk.api.serializers.to_warned_risk_partners_serializers import *
from risk.api.serializers import *
from risk.api.filters import *
from risk.utils.filter_utils import to_warned_filters_for_views

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
    
class ToWarnedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = ToWarnedRiskPartnerListSerializer
    filterset_class = ToWarnedRiskPartnerFilter
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

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            # to_warned_filters_for_views()
            Q(partner_contracts__contract_leases__risk_status='ihtar_cekilecek')
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

class DepositeToWarnedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = DepositeToWarnedRiskPartnerListSerializer
    filterset_class = ToWarnedRiskPartnerFilter
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

        # date_ago = (now() - timedelta(days=67)).date()
        # print("67 gün önceki tarih:", date_ago)

        today = now().date()

        custom_related_fields = []
        prefetch_related_fields = ["partner_contracts__contract_leases", "partner_contracts__vendor"]

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            to_warned_filters_for_views() &
            Q(partner_contracts__contract_leases__odenen_yerel__lte=20000)
            #~Q(partner_contracts__contract_leases__lease_trade_transactions__amount_type=0)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"])
        )
        # Get only the payment_date of the installment with sequency=0 for filtering
        queryset = queryset.annotate(
            overdue_days_int=Cast(
                F('partner_contracts__contract_leases__overdue_days'),
                output_field=IntegerField()
            ),
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'partner_contracts__contract_leases__lease_installments__payment_date',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            first_installment_payment=Max(
                'partner_contracts__contract_leases__lease_installments__payment',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'partner_contracts__contract_contract_payments__credit_amount'
            ),
            # total_trade_transactions=Sum(
            #     Case(
            #         When(
            #             partner_contracts__contract_leases__lease_trade_transactions__posting_group_name='Kira',
            #             partner_contracts__contract_leases__lease_trade_transactions__amount_type=0,
            #             then='partner_contracts__contract_leases__lease_trade_transactions__amount'
            #         ),
            #         output_field=models.DecimalField(),
            #     )
            # ),
            # count_trade_transaction=Count(
            #     'partner_contracts__contract_leases__lease_trade_transactions__id'
            # ),
        )
        # .filter(
        #     # (
        #     #     Q(first_installment_payment_date=F('expected_payment_date')) |
        #     #     Q(first_installment_payment__lte=20000)
        #     # ) |
        #     Q(first_installment_payment_date=F('expected_payment_date')) |
        #     Q(total_contract_payments__lte=20000) |
        #     Q(total_trade_transactions__lte=20000) |
        #     (
        #         Q(count_trade_transaction__gt=0) &
        #         Q(partner_contracts__contract_leases__is_last_project=True) &
        #         Q(partner_contracts__contract_leases__odenen_yerel__lte=20000)
        #     )
        # )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class KepToWarnedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = KepToWarnedRiskPartnerListSerializer
    filterset_class = ToWarnedRiskPartnerFilter
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

        today = now().date()

        custom_related_fields = []
        prefetch_related_fields = ["partner_contracts__contract_leases", "partner_contracts__vendor"]

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            to_warned_filters_for_views() &
            #Q(partner_contracts__contract_leases__lease_trade_transactions__amount_type=0) &
            Q(is_turkkep=True) &
            Q(partner_contracts__contract_leases__odenen_yerel__gt=20000) &
            ~Q(types__contains=["special"])
        ).annotate(
            overdue_days_int=Cast(
                F('partner_contracts__contract_leases__overdue_days'),
                output_field=IntegerField()
            ),
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'partner_contracts__contract_leases__lease_installments__payment_date',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            first_installment_payment=Max(
                'partner_contracts__contract_leases__lease_installments__payment',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'partner_contracts__contract_contract_payments__credit_amount'
            ),
            # total_trade_transactions=Sum(
            #     Case(
            #         When(
            #             partner_contracts__contract_leases__lease_trade_transactions__posting_group_name='Kira',
            #             partner_contracts__contract_leases__lease_trade_transactions__amount_type=0,
            #             then='partner_contracts__contract_leases__lease_trade_transactions__amount'
            #         ),
            #         output_field=models.DecimalField(),
            #     )
            # ),
            # count_trade_transaction=Count(
            #     'partner_contracts__contract_leases__lease_trade_transactions__id'
            # ),
        )
        # .filter(
        #     Q(total_contract_payments__gt=20000)
        #     #Q(total_trade_transactions__gt=20000) |
        #     # (
        #     #     Q(count_trade_transaction__gt=0) &
        #     #     Q(partner_contracts__contract_leases__is_last_project=True) &
        #     #     Q(partner_contracts__contract_leases__odenen_yerel__gt=20000)
        #     # )
        # )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class PostaToWarnedRiskPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = PostaToWarnedRiskPartnerListSerializer
    filterset_class = ToWarnedRiskPartnerFilter
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

        today = now().date()

        custom_related_fields = []
        prefetch_related_fields = ["partner_contracts__contract_leases", "partner_contracts__vendor"]

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            to_warned_filters_for_views() &
            # Q(partner_contracts__contract_leases__lease_trade_transactions__amount_type=0) &
            Q(is_turkkep=False) &
            Q(partner_contracts__contract_leases__odenen_yerel__gt=20000) &
            ~Q(types__contains=["special"])
        ).annotate(
            overdue_days_int=Cast(
                F('partner_contracts__contract_leases__overdue_days'),
                output_field=IntegerField()
            ),
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'partner_contracts__contract_leases__lease_installments__payment_date',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            first_installment_payment=Max(
                'partner_contracts__contract_leases__lease_installments__payment',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'partner_contracts__contract_contract_payments__credit_amount'
            ),
            # total_trade_transactions=Sum(
            #     Case(
            #         When(
            #             partner_contracts__contract_leases__lease_trade_transactions__posting_group_name='Kira',
            #             partner_contracts__contract_leases__lease_trade_transactions__amount_type=0,
            #             then='partner_contracts__contract_leases__lease_trade_transactions__amount'
            #         ),
            #         output_field=models.DecimalField(),
            #     )
            # ),
            # count_trade_transaction=Count(
            #     'partner_contracts__contract_leases__lease_trade_transactions__id'
            # ),
        )
        # .filter(
        #     Q(total_contract_payments__gt=20000) |
        #     Q(total_trade_transactions__gt=20000) |
        #     (
        #         Q(count_trade_transaction__gt=0) &
        #         Q(partner_contracts__contract_leases__is_last_project=True) &
        #         Q(partner_contracts__contract_leases__odenen_yerel__gt=20000)
        #     )
        # )

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

