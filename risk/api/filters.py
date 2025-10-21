from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from risk.api.serializers.risk_partners_serializers import *
from risk.api.serializers.amount_debit_serializers import *
from risk.api.serializers.under_review_serializers import *

class AmountDebitTransactionFilter(FilterSet):
    lease = CharFilter(field_name='lease_code', lookup_expr='icontains')
    partner = CharFilter(field_name='lease__contract__partner__name', lookup_expr='icontains')
    class Meta:
        model = AmountDebitTransaction
        fields = ['uuid']

class UnderReviewFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    bigger_than_100 = CharFilter(method = 'filter_bigger_than_100')
    #project = CharFilter(method = 'filter_project')
    class Meta:
        model = Partner
        fields = ['uuid','name','tc_vkn_no','is_commercial']

    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
    def filter_overdue_amount(self, queryset, overdue_amount, value):
        if value == "true":
            return queryset.filter(partner_contracts__contract_leases__overdue_amount__gt=0)
        else:
            return queryset.filter()
        
    def filter_bigger_than_100(self, queryset, bigger_than_100, value):
        if value == "true":
            return queryset.filter(partner_contracts__contract_leases__overdue_amount__gt=100)
        else:
            return queryset.filter()
    
    def filter_special(self, queryset, special, value):
        if value == "true":
            return queryset.filter(types__contains=["special"])
        else:
            return queryset.exclude(types__contains=["special"])
        
    def filter_barter(self, queryset, barter, value):
        if value == "true":
            return queryset.filter(types__contains=["barter"])
        else:
            return queryset.exclude(types__contains=["barter"])
        
    def filter_virman(self, queryset, virman, value):
        if value == "true":
            return queryset.filter(types__contains=["virman"])
        else:
            return queryset.exclude(types__contains=["virman"])