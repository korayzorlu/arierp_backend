from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter
from django.db.models import QuerySet, Q
from django.db.models.functions import Lower,Upper

from products.models import *

class CategoryFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(method = 'filter_name')

    class Meta:
        model = Category
        fields = ['uuid','name']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))

class ProductFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    category = CharFilter(method = 'filter_category')
    name = CharFilter(method = 'filter_name')

    class Meta:
        model = Product
        fields = ['uuid','category','name']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_category(self, queryset, category, value):
        return queryset.filter(category = value)
    
    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))