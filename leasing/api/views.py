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
    
class LeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company","contract","currency","status","contract__quotation_obj","contract__quotation_obj__quick_quotation"]

        if ordering:
            queryset = Lease.objects.select_related(*custom_related_fields).filter(
                Q(company = active_company.company if active_company else None) &
                vendor_filter_for_serializers(self.request.query_params)
            ).order_by(str(ordering))
        else:
            queryset = Lease.objects.select_related(*custom_related_fields).filter(
                Q(company = active_company.company if active_company else None) &
                vendor_filter_for_serializers(self.request.query_params)
            ).order_by("-activation_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code","contract__partner__name","contract__project","type","activation_date","lease_status","currency__code","project_no","status__name","leasing_type","application_no","current_request","finansman_kurum","bbsn"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset

class ActiveLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = ActiveLeaseListSerializer
    filterset_class = ActiveLeaseFilter
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
            # (
            #     Q(lease_status='aktiflestirildi') |
            #     Q(lease_status='planlandi') |
            #     Q(lease_status='durduruldu') |
            #     Q(lease_status='feshedildi') |
            #     Q(lease_status='devredildi')
            # ) &
            Q(is_last_project=True)
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


class LeaseSummaryList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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

        today = date.today()

        latest_payment_date_sq = Installment.objects.select_related("lease").filter(
            lease=OuterRef('pk')
        ).order_by('-sequency').values('payment_date')[:1]

        queryset = Lease.objects.select_related("company").prefetch_related("lease_installments").filter(
            Q(company=active_company.company if active_company else None) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu') |
                Q(lease_status='feshedildi') |
                Q(lease_status='devredildi')
            ) &
            Q(is_last_project=True)
        )

        queryset1 = queryset.annotate(
            latest_installment_payment_date=Subquery(latest_payment_date_sq)
        ).exclude(
            Q(lease_status='aktiflestirildi') &
            Q(latest_installment_payment_date__gte=today)
        )

        status_counts = (
            queryset1
            .values('lease_status')
            .annotate(count=Count('id'))
        )

        queryset2 = queryset.annotate(
            latest_installment_payment_date=Subquery(latest_payment_date_sq)
        ).filter(
            Q(company=active_company.company if active_company else None) &
            Q(lease_status='aktiflestirildi') &
            Q(is_last_project=True) &
            Q(latest_installment_payment_date__gte=today)
        )

        # Prepare result as dict for each status
        result = {
            'aktiflestirildi': 0,
            'planlandi': 0,
            'durduruldu': 0,
            'feshedildi': 0,
            'devredilecek': 0,
            'devredildi': 0
        }

        for item in status_counts:
            result[item['lease_status']] = item['count']
        
        if queryset2:
            result['devredilecek'] = queryset2.count()

        return Response(result)
    
class PortfolioSummaryList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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

        today = datetime.today()
        months = []
        for i in range(12):
            date = today - relativedelta(months=i)
            months.append(date.strftime("%m/%Y"))

        months.reverse()
        
        result = []

        for month in months:
            # print(f"start date: {datetime.strptime(month, "%m/%Y").strftime("%Y-%m-01")} | end date: {(datetime.strptime(month, "%m/%Y") + relativedelta(months=1)).strftime("%Y-%m-01")}")
            queryset = Lease.objects.filter(
                Q(company=active_company.company if active_company else None) &
                (
                    Q(lease_status='aktiflestirildi') |
                    Q(lease_status='planlandi') |
                    Q(lease_status='durduruldu') |
                    Q(lease_status='devredildi')
                ) &
                # Q(activation_date__gte=month.split('/')[1] + '-' + month.split('/')[0] + '-01') &
                Q(activation_date__gte=datetime.strptime(month, "%m/%Y").strftime("%Y-%m-01")) &
                Q(activation_date__lt=(datetime.strptime(month, "%m/%Y") + relativedelta(months=1)).strftime("%Y-%m-01")) &
                Q(is_last_project=True)
            ).annotate(
                total_installments_amount=Sum('lease_installments__amount')
            ).aggregate(
                total_amount=Sum('total_installments_amount')
            )
            result.append({
                'month': month,
                'total': queryset['total_amount'] or Decimal('0.00')
            })
        
        return Response(result)

class TerminatedSummaryList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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

        today = datetime.today().date()
        start_date = today - timedelta(days=29)

        queryset = Lease.objects.filter(
            Q(company=active_company.company if active_company else None) &
            Q(lease_status='feshedildi') &
            Q(lease_status_update_date__gte=start_date) &
            Q(lease_status_update_date__lte=today)
        ).order_by('lease_status_update_date')

        lease_daily_counts = (
            queryset
            .annotate(day=TruncDate('lease_status_update_date'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Prepare result as dict for each status
        result = []
        for i in range(30):
            day = start_date + timedelta(days=i)
            count = next((item['count'] for item in lease_daily_counts if item['day'] == day), 0)
            result.append({'day': day, 'count': count})

        return Response(result)

class InstallmentsSummaryListt(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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

        

        today = datetime.today().date()
        start_date = today - timedelta(days=29)

        installments = Installment.objects.filter(
            Q(company=active_company.company if active_company else None) &
            (
                Q(lease__lease_status='aktiflestirildi') |
                Q(lease__lease_status='planlandi') |
                Q(lease__lease_status='durduruldu')
            ) &
            Q(payment_date__gte=start_date) &
            Q(payment_date__lte=today)
        ).order_by('payment_date')

        installment_daily_amounts = (
            installments
            .annotate(day=TruncDate('payment_date'))
            .values('day')
            .annotate(amount=Sum('amount'))
            .order_by('day')
        )

        # Prepare result as dict for each status
        result = []
        for i in range(30):
            day = start_date + timedelta(days=i)
            amount = next((item['amount'] for item in installment_daily_amounts if item['day'] == day), 0)
            result.append({'day': day, 'amount': amount})

        return Response(result)
    
class InstallmentsSummaryList(ModelViewSet, QueryListAPIView):
    serializer_class = LeaseListSerializer
    filterset_class = LeaseFilter
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

        #get_exhange_rate_for_date()

        month_count = request.query_params.get('month', 12)

        today = datetime.today()
        months = []
        for i in range(int(month_count)):
            date = today - relativedelta(months=i)
            months.append(date.strftime("%m/%Y"))

        months.reverse()
        
        result = []

        for month in months:
            queryset = Installment.objects.filter(
                Q(company=active_company.company if active_company else None) &
                (
                    Q(lease__lease_status='aktiflestirildi') |
                    Q(lease__lease_status='planlandi') |
                    Q(lease__lease_status='durduruldu')
                ) &
                Q(payment_date__gte=datetime.strptime(month, "%m/%Y").strftime("%Y-%m-01")) &
                Q(payment_date__lt=(datetime.strptime(month, "%m/%Y") + relativedelta(months=1)).strftime("%Y-%m-01"))
            ).aggregate(
                total_amount=Sum('amount')
            )
            result.append({
                'month': month,
                'amount': queryset.get('total_amount', Decimal('0.00'))
            })

        return Response(result)

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
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["currency"]

        today = date.today()

        queryset = BankActivity.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None)
        ).order_by("-created_date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["currency__code","bank","bank_account_no","process_date","process_type","receipt_no","description"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class AccountNoList(ModelViewSet, QueryListAPIView):
    serializer_class = BankActivityListSerializer
    filterset_class = BankActivityFilter
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

        result = BankActivity.objects.filter(
            company=active_company.company if active_company else None
        ).values_list(
            'finmaks_transaction__bank_account__account_no', flat=True
        ).distinct()

        return Response(result)

class BankActivityLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = BankActivityLeaseListSerializer
    filterset_class = BankActivityLeaseFilter
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
      
class RiskPartnerKDVList(ModelViewSet, QueryListAPIView):
    serializer_class = RiskPartnerKDVListSerializer
    filterset_class = RiskPartnerKDVFilter
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
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=True) &
            Q(partner_contracts__contract_leases__is_under_review=False)
            #Q(partner_contracts__contract_leases__overdue_amount__gt=100)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(types__contains=["special"])

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["name","tc_vkn_no","crm_code"]
            
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
            project_filter_for_views(self.request.query_params) &
            (
                Q(partner_contracts__contract_leases__lease_status='planlandi')
            ) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) &
            Q(partner_contracts__contract_leases__paid_rate__gte=30) &
            Q(partner_contracts__contract_leases__overdue_amount__lte=100)
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
 

class DepositPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = DepositPartnerListSerializer
    filterset_class = DepositPartnerFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['name','tc_vkn_no','crm_code']
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
        is_kdv = self.request.query_params.get('kdv')

        custom_related_fields = []
        prefetch_related_fields = ["partner_contracts__contract_leases", "partner_contracts__vendor"]

        contracts_without_warning = Contract.objects.filter(partner=OuterRef('pk')).filter(contract_warning_notices__isnull=True)

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__paid__lte=10000) &
            Q(partner_contracts__contract_leases__paid__gte=1000) &
            Q(partner_contracts__contract_leases__overdue_days__gt=0) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=100)
        ).exclude(types__contains=["special"]).distinct()

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["country__name","billing__country"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
  
class AgreedTerminatedPartnerList(ModelViewSet, QueryListAPIView):
    serializer_class = AgreedTerminatedPartnerListSerializer
    filterset_class = AgreedTerminatedPartnerFilter
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

        # Use prefetch_related for partner_contracts to reduce DB hits
        custom_related_fields = []
        prefetch_related_fields = ["partner_contracts__contract_leases", "partner_contracts__contract_warning_notices", "partner_contracts__vendor"]

        queryset = Partner.objects.select_related(*custom_related_fields).prefetch_related(*prefetch_related_fields).filter(
            Q(company=active_company.company if active_company else None) &
            vendor_filter_for_views(self.request.query_params) &
            Q(partner_contracts__contract_leases__is_agreed_terminated=True)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(types__contains=["special"]).distinct()

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
    # # pagination_class = DatatablesPagination
    def get_pagination_class(self):
        paginate = self.request.query_params.get('paginate')
        if paginate == 'false':
            return None
        return DatatablesPagination

    @property
    def pagination_class(self):
        return self.get_pagination_class()
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

        custom_related_fields = ["country","billing_country"]

        distinct_authors = Contract.objects.values_list('project', flat=True).distinct()
        for distinct_author in distinct_authors:
            print(distinct_author)

        queryset = Partner.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=100) &
            Q(partner_contracts__contract_leases__overdue_days__lte=30) &
            #Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
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