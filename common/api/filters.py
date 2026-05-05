
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from common.models import *

class ExchangeRateFilter(FilterSet):
    base_currency = CharFilter(field_name='base_currency__code', lookup_expr='icontains')
    target_currency = CharFilter(field_name='target_currency__code', lookup_expr='icontains')

    class Meta:
        model = ExchangeRate
        fields = ['id','date','forex_buying','forex_selling']

