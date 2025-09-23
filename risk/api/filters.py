from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class AmountDebitTransactionFilter(FilterSet):
    lease = CharFilter(field_name='lease_code', lookup_expr='icontains')
    partner = CharFilter(field_name='lease__contract__partner__name', lookup_expr='icontains')
    class Meta:
        model = AmountDebitTransaction
        fields = ['uuid']