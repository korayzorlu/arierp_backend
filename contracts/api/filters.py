from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter

from .serializers import *

class ContractFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    quotation = CharFilter(field_name='quotation_obj__code', lookup_expr='exact')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['uuid','code','contract_id','project','customer_representative']
    
    

class ContractPaymentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    contract = CharFilter(method = 'filter_contract')
    contract_id = CharFilter(field_name='contract__contract_id', lookup_expr='exact')
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
    
class WarningNoticeFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    contract = CharFilter(method = 'filter_contract')
    document_id = CharFilter(method = 'filter_document_id')
    risk_id = CharFilter(method = 'filter_risk_id')
    customer_id = CharFilter(method = 'filter_customer_id')
    process_start_date = CharFilter(method = 'filter_process_start_date')
    service_date = CharFilter(method = 'filter_service_date')
    official_cancellation_date = CharFilter(method = 'filter_official_cancellation_date')
    state = CharFilter(method = 'filter_state')
    approval_state = CharFilter(method = 'filter_approval_state')
    currency = CharFilter(method = 'filter_currency')
    partner_name = CharFilter(method = 'filter_partner_name')
    partner_crm_code = CharFilter(method = 'filter_partner_crm_code')

    class Meta:
        model = WarningNotice
        fields = ['uuid','document_id','risk_id','customer_id','process_start_date','service_date','official_cancellation_date','state','approval_state']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_contract(self, queryset, contract, value):
        return queryset.filter(contract__code = str(value))
    
    def filter_currency(self, queryset, currency, value):
        return queryset.annotate(lowercase=Lower('contract__currency__code'),uppercase=Upper('contract__currency__code')).filter(Q(lowercase = value) | Q(uppercase = value))
    
    def filter_partner_name(self, queryset, partner, value):
        return queryset.annotate(lowercase=Lower('contract__partner__name'),uppercase=Upper('contract__partner__name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
    def filter_partner_crm_code(self, queryset, partner_crm_code, value):
        return queryset.filter(contract__partner__crm_code = str(value))