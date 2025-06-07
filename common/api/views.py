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

class CountryList(ModelViewSet, QueryListAPIView):
    serializer_class = CountryListSerializer
    filterset_fields = {
                        'name': ['exact','in', 'isnull'],
    }
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        custom_related_fields = []

        queryset = Country.objects.select_related(*custom_related_fields).filter().order_by("id")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["name","formal_name","iso2","iso3","dial_code"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset

class CityFilter(FilterSet):
    id = CharFilter(method = 'filter_id')
    name = CharFilter(method = 'filter_name')

    class Meta:
        model = City
        fields = ['id','name']

    def filter_id(self, queryset, id, value):
        return queryset.filter(id = int(value))
    
    def filter_name(self, queryset, name, value):
        print(value)
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))

class CityList(ModelViewSet, QueryListAPIView):
    serializer_class = CityListSerializer
    #filterset_fields = {}
    filterset_class = CityFilter
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    required_subscription = "free"
    permission_classes = [SubscriptionPermission,BlockBrowserAccessPermission]
    
    def get_queryset(self):
        country_iso2 = self.request.query_params.get('country')

        custom_related_fields = ["country"]

        queryset = City.objects.select_related(*custom_related_fields).filter(country__iso2 = country_iso2).order_by("name")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["name","country__name"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class CurrencyList(ModelViewSet, QueryListAPIView):
    serializer_class = CurrencyListSerializer
    filterset_fields = {
                        'code': ['exact','in', 'isnull'],
    }
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        custom_related_fields = []

        queryset = Currency.objects.select_related(*custom_related_fields).filter().order_by("code")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["code","name","symbol"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset
    
class ImportProcessList(ModelViewSet, QueryListAPIView):
    serializer_class = ImportProcessListSerializer
    filterset_fields = {
                        'user': ['exact','in', 'isnull'],
    }
    filter_backends = [OrderingFilter,DjangoFilterBackend]
    ordering_fields = '__all__'
    required_subscription = "free"
    permission_classes = [SubscriptionPermission]
    
    def get_queryset(self):
        custom_related_fields = ["user"]
        
        queryset = ImportProcess.objects.select_related(*custom_related_fields).filter(user = self.request.user, status = "in_progress").order_by("user__email")

        query = self.request.query_params.get('search[value]', None)
        if query:
            search_fields = ["model_name","status","user__email"]
            
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": query})
            
            queryset = queryset.filter(q_objects)
        return queryset