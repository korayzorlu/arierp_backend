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

class PartnerFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    country = CharFilter(field_name='country__name', lookup_expr='icontains')
    city = CharFilter(field_name='city__name', lookup_expr='icontains')

    class Meta:
        model = Partner
        fields = ['uuid','name','crm_code','customer_code','tc_vkn_no']