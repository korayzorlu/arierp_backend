from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,Exists,IntegerField,Sum,OuterRef,Subquery,ExpressionWrapper,DateField
from trade.models import TradeTransaction
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


from risk.api.serializers.terminated_leases_serializers import *
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
    
class TerminatedLeaseOrderingFilter(OrderingFilter):
    # 'terminated_date' modelde gerçek bir alan olduğu için annotate ismi çakışıyor;
    # dışarıdan gelen ordering parametresini annotate alanına yönlendiriyoruz.
    ordering_field_map = {
        'terminated_date': 'terminated_date_annot',
        '-terminated_date': '-terminated_date_annot',
        'last_refund_date': 'last_refund_date_annot',
        '-last_refund_date': '-last_refund_date_annot',
    }

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if ordering:
            ordering = [self.ordering_field_map.get(field, field) for field in ordering]
        return ordering


class TerminatedLeaseList(ModelViewSet, QueryListAPIView):
    serializer_class = TerminatedLeaseListSerializer
    filterset_class = TerminatedLeaseFilter
    filter_backends = [TerminatedLeaseOrderingFilter,DjangoFilterBackend]
    ordering_fields = ['code','activation_date','lease_status','currency__code','project_no','status__name','leasing_type','application_no',
                       'current_request','finansman_kurum','bbsn','lease_status_update_date','terminated_date','last_refund_date']
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
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        if hasattr(self, '_cached_queryset'):
            return self._cached_queryset
        active_company_uuid = self.request.query_params.get('ac')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()
        ordering = self.request.query_params.get('ordering')
        
        custom_related_fields = ["company","contract","currency","status","contract__quotation_obj","contract__quotation_obj__quick_quotation"]

        queryset = Lease.objects.select_related(*custom_related_fields).filter(
            Q(company = active_company.company if active_company else None) &
            #vendor_filter_for_serializers(self.request.query_params) &
            Q(lease_status='feshedildi') &
            Q(is_last_project=True) &
            Q(lease_trade_transactions__posting_group_name='Fesih İadesi')
        ).annotate(
            refund_amount=Sum(
                Case(
                    When(
                        lease_trade_transactions__posting_group_name='Fesih İadesi',
                        then='lease_trade_transactions__amount'
                    ),
                    output_field=models.DecimalField(),
                )
            ),
            terminated_date_annot=Subquery(
                TradeTransaction.objects.filter(
                    lease=OuterRef('pk'),
                    posting_group_name='Fesih İadesi',
                    amount_type='0',
                ).exclude(delete_status__in=['2']).values('due_date')[:1]
            ),
            last_refund_date_annot=ExpressionWrapper(
                Subquery(
                    TradeTransaction.objects.filter(
                        lease=OuterRef('pk'),
                        posting_group_name='Fesih İadesi',
                        amount_type='0',
                    ).exclude(delete_status__in=['2']).values('due_date')[:1]
                ) + timedelta(days=180),
                output_field=DateField(),
            )
        ).filter(
            Q(refund_amount__gt=0)
        ).exclude(contract__partner__types__contains=["special"]).distinct()

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["contract__code","contract__partner__name","contract__project","type","activation_date","lease_status","currency__code","project_no","status__name","leasing_type","application_no","current_request","finansman_kurum","bbsn"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        self._cached_queryset = queryset
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        objects = page if page is not None else queryset

        # Tüm main_lease_id'leri topla, tek sorguda çek
        main_lease_ids = [obj.main_lease_id for obj in objects if obj.main_lease_id]
        all_old_leases = Lease.objects.filter(
            main_lease_id__in=main_lease_ids
        ).annotate(
            lease_id_int=Cast('lease_id', IntegerField())
        ).only('uuid', 'code', 'main_lease_id').order_by('-lease_id_int')


        serializer = self.get_serializer(
            objects, many=True,
            context={**self.get_serializer_context()}
        )

        if page is not None:
            response = self.get_paginated_response(serializer.data)
            # Filtre seçenekleri her zaman filtrelenmemiş queryset'ten üretilir;
            # aksi halde bir proje seçilince listede sadece o proje kalır ve
            # çoklu seçim yapılamaz.
            options_queryset = self.get_queryset()
            projects = list(
                options_queryset.exclude(item__isnull=True)
                        .order_by('item__stock_name')
                        .values('item__stock_name', 'item__uuid')
                        .distinct()
            )
            vendors = list(
                options_queryset.exclude(contract__vendor__isnull=True)
                        .order_by('contract__vendor__name')
                        .values('contract__vendor__name', 'contract__vendor__uuid')
                        .distinct()
            )
            response.data['projects'] = projects
            response.data['vendors'] = vendors
            return response
        return Response(serializer.data)

