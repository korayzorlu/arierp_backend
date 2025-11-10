
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from accounting.models import *

class PaymentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    type = CharFilter(method = 'filter_type')
    partner = CharFilter(method = 'filter_partner')

    class Meta:
        model = Payment
        fields = ['uuid','type','partner']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_type(self, queryset, type, value):
        return queryset.filter(type = value)
    
    def filter_partner(self, queryset, partner, value):
        return queryset.filter(partner__uuid = value)
    
class TrialBalanceFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    account_code = CharFilter(field_name='account_code', lookup_expr='icontains')
    main_account_code = CharFilter(method = 'filter_main_account_code')
    account_name = CharFilter(field_name='account_name', lookup_expr='icontains')

    class Meta:
        model = TrialBalance
        fields = ['uuid','account_id','account_code','account_code_trim','account_name']

    def filter_main_account_code(self, queryset, main_account_code, value):
        if value == 'all':
            return queryset
        return queryset.filter(main_account_code = value)