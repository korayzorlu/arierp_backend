from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django.utils.timezone import make_aware

from datetime import datetime
from decimal import Decimal

from .serializers import *

class TradeAccountFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    partner = CharFilter(method = 'filter_partner')
    account_id = CharFilter(method = 'filter_account_id')
    name = CharFilter(method = 'filter_name')
    crm_id = CharFilter(method = 'filter_crm_id')
    crm_type = CharFilter(method = 'filter_crm_type')

    class Meta:
        model = TradeAccount
        fields = ['uuid','partner__name','account_id','name','crm_id','crm_type']
    
    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
class TradeTransactionFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    lease = CharFilter(field_name='lease__code', lookup_expr='icontains')
    posting_group_name = CharFilter(field_name='posting_group__name', lookup_expr='icontains')
    description = CharFilter(field_name='description', lookup_expr='icontains')
    document_no = CharFilter(field_name='document_no', lookup_expr='icontains')

    class Meta:
        model = TradeTransaction
        fields = ['uuid','trade_transaction_id','posting_group_id','posting_group_name','description','document_no','amount_type','due_date','record_date']

