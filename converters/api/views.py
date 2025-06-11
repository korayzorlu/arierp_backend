from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet, Q
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

class BankaHareketiFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    gonderen_unvani = CharFilter(method = 'filter_gonderen_unvani')

    class Meta:
        model = BankaHareketi
        fields = ['uuid','gonderen_unvani']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_gonderen_unvani(self, queryset, gonderen_unvani, value):
        return queryset.annotate(lowercase=Lower('gonderen_unvani'),uppercase=Upper('gonderen_unvani')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
class BankaHareketiList(ModelViewSet, QueryListAPIView):
    serializer_class = BankaHareketiListSerializer
    filterset_class = BankaHareketiFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company"]

        queryset = BankaHareketi.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("gonderen_unvani")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["gonderen_unvani","musteri_unvani","aciklama","ucuncu_sahis_mi"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class BankaTahsilatiFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    gonderen_unvani = CharFilter(method = 'filter_gonderen_unvani')

    class Meta:
        model = BankaTahsilati
        fields = ['uuid','gonderen_unvani']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_gonderen_unvani(self, queryset, gonderen_unvani, value):
        return queryset.annotate(lowercase=Lower('gonderen_unvani'),uppercase=Upper('gonderen_unvani')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
class BankaTahsilatiList(ModelViewSet, QueryListAPIView):
    serializer_class = BankaTahsilatiListSerializer
    filterset_class = BankaTahsilatiFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company"]

        queryset = BankaTahsilati.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("gonderen_unvani")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["gonderen_unvani","tc_vkn_no"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class BankaTahsilatiOdooFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    gonderen_unvani = CharFilter(method = 'filter_gonderen_unvani')

    class Meta:
        model = BankaTahsilatiOdoo
        fields = ['uuid','gonderen_unvani']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_gonderen_unvani(self, queryset, gonderen_unvani, value):
        return queryset.annotate(lowercase=Lower('gonderen_unvani'),uppercase=Upper('gonderen_unvani')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
class BankaTahsilatiOdooList(ModelViewSet, QueryListAPIView):
    serializer_class = BankaTahsilatiOdooListSerializer
    filterset_class = BankaTahsilatiOdooFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    pagination_class = DatatablesPagination
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        active_company_uuid = self.request.query_params.get('active_company')
        active_company = self.request.user.user_companies.filter(uuid = active_company_uuid).first()

        custom_related_fields = ["company"]

        queryset = BankaTahsilatiOdoo.objects.select_related(*custom_related_fields).filter(company = active_company.company if active_company else None).order_by("gonderen_unvani")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["gonderen_unvani","tc_vkn_no"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset