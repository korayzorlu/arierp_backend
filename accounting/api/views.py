from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q
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

class AccountFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    type = CharFilter(method = 'filter_type')
    partner = CharFilter(method = 'filter_partner')

    class Meta:
        model = Account
        fields = ['uuid','type','partner']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_type(self, queryset, type, value):
        return queryset.filter(type__code = value)
    
    def filter_partner(self, queryset, partner, value):
        return queryset.filter(partner__uuid = value)
    
class AccountList(ModelViewSet, QueryListAPIView):
    serializer_class = AccountListSerializer
    # filterset_fields = {
    #                     'uuid': ['exact','in', 'isnull'],
    #                     'company': ['exact','in', 'isnull'],
    # }
    filterset_class = AccountFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["partner","currency"]

        queryset = Account.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("partner__name")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["partner__name","currency__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class TransactionFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    type = CharFilter(method = 'filter_type')
    account = CharFilter(method = 'filter_account')
    currency = CharFilter(method = 'filter_currency')

    class Meta:
        model = Transaction
        fields = ['uuid','type','account__partner','account__currency']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_type(self, queryset, type, value):
        return queryset.filter(type = value)
    
    def filter_account(self, queryset, account, value):
        return queryset.filter(account__uuid = value)
    
    def filter_currency(self, queryset, account__currency, value):
        return queryset.filter(account__currency__code = value)
    
class TransactionList(ModelViewSet, QueryListAPIView):
    serializer_class = TransactionListSerializer
    # filterset_fields = {
    #                     'uuid': ['exact','in', 'isnull'],
    #                     'company': ['exact','in', 'isnull'],
    # }
    filterset_class = TransactionFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["account__partner","account__currency"]

        queryset = Transaction.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("-date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["account__partner__name","account__currency__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class InvoiceFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    type = CharFilter(method = 'filter_type')
    partner = CharFilter(method = 'filter_partner')

    class Meta:
        model = Invoice
        fields = ['uuid','type','partner']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_type(self, queryset, type, value):
        return queryset.filter(type = value)
    
    def filter_partner(self, queryset, partner, value):
        return queryset.filter(partner__uuid = value)
    
class InvoiceList(ModelViewSet, QueryListAPIView):
    serializer_class = InvoiceListSerializer
    filterset_class = InvoiceFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["partner","currency"]

        queryset = Invoice.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("-date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["partner__name","currency__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class PaymentList(ModelViewSet, QueryListAPIView):
    serializer_class = PaymentListSerializer
    filterset_class = PaymentFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["partner","currency"]

        queryset = Payment.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("-date")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["partner__name","currency__code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset