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

class ContractPaymentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    contract = CharFilter(method = 'filter_contract')
    currency = CharFilter(method = 'filter_currency')
    ledger_account_name = CharFilter(method = 'filter_ledger_account_name')
    group_name = CharFilter(method = 'filter_group_name')
    account_name = CharFilter(method = 'filter_account_name')
    user_name = CharFilter(method = 'filter_user_name')
    description = CharFilter(method = 'filter_description')

    class Meta:
        model = ContractPayment
        fields = ['uuid','trn_id','trn_from_id','ledger_account_id','ledger_account_name','trade_account_code','type','posting_type','group_name','account_code','account_name']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_contract(self, queryset, contract, value):
        return queryset.filter(contract__code = str(value))
    
    def filter_currency(self, queryset, currency, value):
        return queryset.annotate(lowercase=Lower('currency__code'),uppercase=Upper('currency__code')).filter(Q(lowercase = value) | Q(uppercase = value))
    
    def filter_ledger_account_name(self, queryset, ledger_account_name, value):
        return queryset.annotate(lowercase=Lower('ledger_account_name'),uppercase=Upper('ledger_account_name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
    def filter_group_name(self, queryset, group_name, value):
        return queryset.annotate(lowercase=Lower('group_name'),uppercase=Upper('group_name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
    def filter_account_name(self, queryset, account_name, value):
        return queryset.annotate(lowercase=Lower('account_name'),uppercase=Upper('account_name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
    def filter_user_name(self, queryset, user_name, value):
        return queryset.annotate(lowercase=Lower('user_name'),uppercase=Upper('user_name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
    def filter_description(self, queryset, description, value):
        return queryset.annotate(lowercase=Lower('description'),uppercase=Upper('description')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )