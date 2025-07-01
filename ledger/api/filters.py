from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django.utils.timezone import make_aware

from datetime import datetime
from decimal import Decimal

from .serializers import *

class LedgerAccountFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(method = 'filter_name')
    account_id = CharFilter(method = 'filter_account_id')
    code = CharFilter(method = 'filter_code')
    currency = CharFilter(method = 'filter_currency')

    class Meta:
        model = LedgerAccount
        fields = ['uuid','account_id','name','code','currency__code']
    
    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))