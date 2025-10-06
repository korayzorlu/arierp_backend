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

class PartnerAdvanceFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    tc_vkn_no = CharFilter(field_name='tc_vkn_no', lookup_expr='exact')
    crm_code = CharFilter(field_name='crm_code', lookup_expr='exact')

    class Meta:
        model = Partner
        fields = ['uuid']

class BankAccountFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    class Meta:
        model = FinmaksBankAccount
        fields = ['uuid']

class BankAccountTransactionFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    class Meta:
        model = FinmaksTransaction
        fields = ['uuid']