from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter

from .serializers import *

class ContractFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    code = CharFilter(method = 'filter_code')

    class Meta:
        model = Contract
        fields = ['uuid','code']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_code(self, queryset, code, value):
        return queryset.filter(code = value)
    