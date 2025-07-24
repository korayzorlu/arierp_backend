from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
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
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    leaseflex_automation = CharFilter(method = 'filter_leaseflex_automation')
    overdue = CharFilter(method = 'filter_overdue')

    class Meta:
        model = Lease
        fields = ['uuid','code','activation_date','vade','leasing_rate','vat','leaseflex_automation']

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
    
    def filter_overdue_amount(self, queryset, overdue_amount, value):
        if value == "true":
            return queryset.annotate(
                total_overdue=Sum('lease_installments__overdue_amount')
            ).filter(total_overdue__gt=0)
        else:
            return queryset.annotate(
                total_overdue=Sum('lease_installments__overdue_amount')
            ).filter(Q(total_overdue__lte=0) | Q(total_overdue__isnull=True))
        
    def filter_leaseflex_automation(self, queryset, leaseflex_automation, value):
        if value == "true":
            return queryset.filter(leaseflex_automation = True)
        else:
            return queryset.filter(leaseflex_automation = False)
        
    def filter_overdue(self, queryset, overdue, value):
        if value:
            return queryset.filter(overdue_amount__gt=0)
        else:
            return queryset.filter()
    
class InstallmentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    lease_id = CharFilter(method = 'filter_lease_id')
    lease = CharFilter(method = 'filter_lease')
    contract = CharFilter(method = 'filter_contract')
    partner = CharFilter(method = 'filter_partner')
    currency = CharFilter(method = 'filter_currency')
    sequency = CharFilter(method = 'filter_sequency')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')

    class Meta:
        model = Installment
        fields = ['uuid','sequency','payment_date']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_lease(self, queryset, lease, value):
        return queryset.filter(lease__code = value)
    
    def filter_lease_id(self, queryset, lease_id, value):
        return queryset.filter(lease__uuid = value)
    
    def filter_contract(self, queryset, contract, value):
        return queryset.filter(lease__contract__code = value)
    
    def filter_partner(self, queryset, partner, value):
        return queryset.filter(lease__contract__partner__code = value)
    
    def filter_currency(self, queryset, currency, value):
        return queryset.annotate(lowercase=Lower('currency__code'),uppercase=Upper('currency__code')).filter(Q(lowercase = value) | Q(uppercase = value))
    
    def filter_sequency(self, queryset, sequency, value):
        return queryset.filter(sequency = value)
    
    def filter_overdue_amount(self, queryset, overdue_amount, value):
        if value == "true":
            return queryset.filter(overdue_amount__gt = 0)
        else:
            return queryset.filter(overdue_amount__gte = 0)
        
class BankActivityFilter(FilterSet):
    class Meta:
        model = BankActivity
        fields = ['uuid','bank','bank_account_no','process_type','receipt_no','description']

class BankActivityLeaseFilter(FilterSet):
    bank_activity = CharFilter(method = 'filter_bank_activity')
    lease = CharFilter(method = 'filter_lease')
    class Meta:
        model = BankActivityLease
        fields = ['uuid','bank_activity','lease']

    def filter_bank_activity(self, queryset, bank_activity, value):
        return queryset.filter(bank_activity__uuid = value)
    
    def filter_lease(self, queryset, lease, value):
        return queryset.filter(lease__lease = value)
    
class RiskPartnerFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    class Meta:
        model = Partner
        fields = ['uuid','name','tc_vkn_no']

    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )