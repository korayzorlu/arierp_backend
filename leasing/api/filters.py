from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django.utils.timezone import make_aware

from datetime import datetime
from decimal import Decimal

from .serializers import *

class LeaseFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    code = CharFilter(method = 'filter_code')
    contract = CharFilter(method = 'filter_contract')
    partner = CharFilter(method = 'filter_partner')
    partner_tc = CharFilter(method = 'filter_partner_tc')
    activation_date = CharFilter(method = 'filter_activation_date')
    quotation = CharFilter(method = 'filter_quotation')
    kof = CharFilter(method = 'filter_kof')
    project = CharFilter(method = 'filter_project')
    block = CharFilter(method = 'filter_block')
    unit = CharFilter(method = 'filter_unit')
    vade = CharFilter(method = 'filter_vade')
    leasing_rate = CharFilter(method = 'filter_leasing_rate')
    vat = CharFilter(method = 'filter_vat')
    currency = CharFilter(method = 'filter_currency')
    lease_status = CharFilter(method = 'filter_lease_status')

    class Meta:
        model = Lease
        fields = ['uuid','code','activation_date','vade','leasing_rate','vat']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_code(self, queryset, code, value):
        return queryset.filter(code = value)
    
    def filter_contract(self, queryset, contract, value):
        return queryset.filter(contract__code = value)
    
    def filter_partner(self, queryset, partner, value):
        return queryset.annotate(lowercase=Lower('contract__quotation_obj__partner__name'),uppercase=Upper('contract__quotation_obj__partner__name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
    def filter_partner_tc(self, queryset, partner_tc, value):
        return queryset.filter(contract__quotation_obj__partner__tc_vkn_no = value)
    
    def filter_activation_date(self, queryset, activation_date, value):
        return queryset.filter(activation_date = make_aware(datetime.strptime(value, "%d.%m.%Y")))
    
    def filter_quotation(self, queryset, quotaiton, value):
        return queryset.filter(contract__quotation_obj__code = value)
    
    def filter_kof(self, queryset, kof, value):
        return queryset.filter(contract__kof = value)
    
    def filter_project(self, queryset, project, value):
        return queryset.annotate(lowercase=Lower('contract__quotation_obj__quick_quotation__project'),uppercase=Upper('contract__quotation_obj__quick_quotation__project')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
    def filter_block(self, queryset, block, value):
        return queryset.annotate(lowercase=Lower('contract__quotation_obj__quick_quotation__block'),uppercase=Upper('contract__quotation_obj__quick_quotation__block')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
    def filter_unit(self, queryset, unit, value):
        return queryset.annotate(lowercase=Lower('contract__quotation_obj__quick_quotation__unit'),uppercase=Upper('contract__quotation_obj__quick_quotation__unit')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
    def filter_vade(self, queryset, vade, value):
        return queryset.filter(vade = value)
    
    def filter_leasing_rate(self, queryset, leasing_rate, value):
        return queryset.filter(leasing_rate = value)
    
    def filter_vat(self, queryset, vat, value):
        return queryset.filter(vat = Decimal(str(value)))
    
    def filter_currency(self, queryset, currency, value):
        return queryset.annotate(lowercase=Lower('currency__code'),uppercase=Upper('currency__code')).filter(Q(lowercase = value) | Q(uppercase = value))
    
    def filter_lease_status(self, queryset, lease_status, value):
        return queryset.annotate(lowercase=Lower('lease_status'),uppercase=Upper('lease_status')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
class InstallmentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    lease = CharFilter(method = 'filter_lease')
    contract = CharFilter(method = 'filter_contract')
    partner = CharFilter(method = 'filter_partner')
    currency = CharFilter(method = 'filter_currency')
    sequency = CharFilter(method = 'filter_sequency')

    class Meta:
        model = Installment
        fields = ['uuid','sequency']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_lease(self, queryset, lease, value):
        return queryset.filter(lease__code = value)
    
    def filter_contract(self, queryset, contract, value):
        return queryset.filter(lease__contract__code = value)
    
    def filter_partner(self, queryset, partner, value):
        return queryset.filter(lease__contract__partner__code = value)
    
    def filter_currency(self, queryset, currency, value):
        return queryset.annotate(lowercase=Lower('currency__code'),uppercase=Upper('currency__code')).filter(Q(lowercase = value) | Q(uppercase = value))
    
    def filter_sequency(self, queryset, sequency, value):
        return queryset.filter(sequency = value)