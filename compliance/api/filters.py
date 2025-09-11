from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class BlackListPersonFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    tc_vkn_passport_no = CharFilter(field_name='tc_vkn_passport_no', lookup_expr='icontains')
    other_names = CharFilter(field_name='other_names', lookup_expr='icontains')
    nationality = CharFilter(field_name='nationality', lookup_expr='icontains')
    birthday = CharFilter(field_name='birthday', lookup_expr='icontains')
    organization = CharFilter(field_name='organization', lookup_expr='icontains')
    date_number = CharFilter(field_name='date_number', lookup_expr='icontains')

    class Meta:
        model = BlackListPerson
        fields = ['uuid']