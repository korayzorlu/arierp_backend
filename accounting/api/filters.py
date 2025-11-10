
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
    
class TrialBalanceContractFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    quotation = CharFilter(field_name='quotation_obj__code', lookup_expr='exact')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')
    is_commercial = CharFilter(method='filter_is_commercial')
    quotation = CharFilter(method='quotation_obj__code', lookup_expr='exact')

    class Meta:
        model = Contract
        fields = ['uuid','code','contract_id','project','customer_representative']

    def filter_is_commercial(self, queryset, is_commercial, value):
        if value == "true":
            value = True
        elif value == "false":
            value = False
        elif value == "all":
            return queryset
        return queryset.filter(partner__is_commercial = value)