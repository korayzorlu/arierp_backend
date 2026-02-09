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
        
class RiskPartnerFilter(FilterSet):
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
        
    # def filter_project(self, queryset, project, value):
    #     if str(value) == "diger":
    #         return queryset.exclude(partner_contracts__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
    #     elif str(value) == "kizilbuk":
    #         return queryset.filter(partner_contracts__vendor__crm_code__in=["11802","20559"])
    #     elif str(value) == "sinpas":
    #         return queryset.filter(partner_contracts__vendor__crm_code__in=["1202"])
    #     elif str(value) == "servet":
    #         return queryset.filter(partner_contracts__vendor__crm_code__in=["6548"])
    #     else:
    #         return queryset.filter(partner_contracts__vendor__crm_code=value)

class ToWarnedRiskPartnerFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    bigger_than_100 = CharFilter(method = 'filter_bigger_than_100')
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
        

class WarnedRiskPartnerFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    bigger_than_100 = CharFilter(method = 'filter_bigger_than_100')
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


class ToTerminatedRiskPartnerFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    bigger_than_100 = CharFilter(method = 'filter_bigger_than_100')
    overdue_terminated = CharFilter(method = 'filter_overdue_terminated')
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
        
    def filter_overdue_terminated(self, queryset, overdue_terminated, value):
        if value == "true":
            today = timezone.localdate()
            return queryset.filter(partner_contracts__contract_warning_notices__official_cancellation_date__lte=datetime.today())
        else:
            return queryset.filter() 

class TerminatedLeaseFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')
    code = CharFilter(field_name='code', lookup_expr='icontains')
    contract = CharFilter(field_name='contract__code', lookup_expr='icontains')
    partner = CharFilter(field_name='contract__partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='contract__partner__tc_vkn_no', lookup_expr='icontains')
    activation_date = CharFilter(field_name='activation_date', lookup_expr='icontains')
    quotation = CharFilter(field_name='contract__quotation_obj__code', lookup_expr='icontains')
    kof = CharFilter(field_name='contract__kof', lookup_expr='icontains')
    project_name = CharFilter(field_name='contract__quotation_obj__quick_quotation__project', lookup_expr='icontains')
    block = CharFilter(field_name='contract__quotation_obj__quick_quotation__block', lookup_expr='icontains')
    unit = CharFilter(field_name='contract__quotation_obj__quick_quotation__unit', lookup_expr='icontains')
    vade = CharFilter(field_name='vade', lookup_expr='icontains')
    leasing_rate = CharFilter(field_name='leasing_rate', lookup_expr='icontains')
    vat = CharFilter(field_name='vat', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    lease_status = CharFilter(method = 'filter_lease_status')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    leaseflex_automation = CharFilter(method = 'filter_leaseflex_automation')
    overdue = CharFilter(method = 'filter_overdue')

    class Meta:
        model = Lease
        fields = ['uuid','code','contract','partner','activation_date','quotation','kof','project_name','block','unit','vade','leasing_rate','vat','currency','lease_status']
    
    def filter_lease_status(self, queryset, lease_status, value):
        if value == 'all':
            return queryset
        else:
            return queryset.filter(lease_status = value)
    
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
        
class ExchangedLeaseFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')
    code = CharFilter(field_name='code', lookup_expr='icontains')
    contract = CharFilter(field_name='contract__code', lookup_expr='icontains')
    partner = CharFilter(field_name='contract__partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='contract__partner__tc_vkn_no', lookup_expr='icontains')
    activation_date = CharFilter(field_name='activation_date', lookup_expr='icontains')
    quotation = CharFilter(field_name='contract__quotation_obj__code', lookup_expr='icontains')
    kof = CharFilter(field_name='contract__kof', lookup_expr='icontains')
    project_name = CharFilter(field_name='contract__quotation_obj__quick_quotation__project', lookup_expr='icontains')
    block = CharFilter(field_name='contract__quotation_obj__quick_quotation__block', lookup_expr='icontains')
    unit = CharFilter(field_name='contract__quotation_obj__quick_quotation__unit', lookup_expr='icontains')
    vade = CharFilter(field_name='vade', lookup_expr='icontains')
    leasing_rate = CharFilter(field_name='leasing_rate', lookup_expr='icontains')
    vat = CharFilter(field_name='vat', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    lease_status = CharFilter(method = 'filter_lease_status')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    leaseflex_automation = CharFilter(method = 'filter_leaseflex_automation')
    overdue = CharFilter(method = 'filter_overdue')

    class Meta:
        model = Lease
        fields = ['uuid','code','contract','partner','activation_date','quotation','kof','project_name','block','unit','vade','leasing_rate','vat','currency','lease_status']
    
    def filter_lease_status(self, queryset, lease_status, value):
        if value == 'all':
            return queryset
        else:
            return queryset.filter(lease_status = value)
    
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

class TufeExchangedLeaseFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')
    code = CharFilter(field_name='code', lookup_expr='icontains')
    contract = CharFilter(field_name='contract__code', lookup_expr='icontains')
    partner = CharFilter(field_name='contract__partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='contract__partner__tc_vkn_no', lookup_expr='icontains')
    activation_date = CharFilter(field_name='activation_date', lookup_expr='icontains')
    quotation = CharFilter(field_name='contract__quotation_obj__code', lookup_expr='icontains')
    kof = CharFilter(field_name='contract__kof', lookup_expr='icontains')
    project_name = CharFilter(field_name='contract__quotation_obj__quick_quotation__project', lookup_expr='icontains')
    block = CharFilter(field_name='contract__quotation_obj__quick_quotation__block', lookup_expr='icontains')
    unit = CharFilter(field_name='contract__quotation_obj__quick_quotation__unit', lookup_expr='icontains')
    vade = CharFilter(field_name='vade', lookup_expr='icontains')
    leasing_rate = CharFilter(field_name='leasing_rate', lookup_expr='icontains')
    vat = CharFilter(field_name='vat', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    lease_status = CharFilter(method = 'filter_lease_status')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    leaseflex_automation = CharFilter(method = 'filter_leaseflex_automation')
    overdue = CharFilter(method = 'filter_overdue')

    class Meta:
        model = Lease
        fields = ['uuid','code','contract','partner','activation_date','quotation','kof','project_name','block','unit','vade','leasing_rate','vat','currency','lease_status']
    
    def filter_lease_status(self, queryset, lease_status, value):
        if value == 'all':
            return queryset
        else:
            return queryset.filter(lease_status = value)
    
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



class TomorrowPartnerFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    tomorrow = CharFilter(method = 'filter_tomorrow')
    class Meta:
        model = Partner
        fields = ['uuid','name','tc_vkn_no','is_commercial']

    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
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
        
class TodayPartnerFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    today = CharFilter(method = 'filter_today')
    class Meta:
        model = Partner
        fields = ['uuid','name','tc_vkn_no','is_commercial']

    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(
            Q(lowercase__icontains = value) |
            Q(uppercase__icontains = value)
        )
    
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
        


class ToBeTransferredFilter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    bigger_than_100 = CharFilter(method = 'filter_bigger_than_100')
    the_project = CharFilter(method = 'filter_the_project')
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

    def filter_the_project(self, queryset, the_project, value):
        print("the_project",value)
        return queryset.filter(partner_contracts__project_obj__uuid=value) 


class OverdueLeaseFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')
    code = CharFilter(field_name='code', lookup_expr='icontains')
    contract = CharFilter(field_name='contract__code', lookup_expr='icontains')
    partner = CharFilter(field_name='contract__partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='contract__partner__tc_vkn_no', lookup_expr='icontains')
    activation_date = CharFilter(field_name='activation_date', lookup_expr='icontains')
    quotation = CharFilter(field_name='contract__quotation_obj__code', lookup_expr='icontains')
    kof = CharFilter(field_name='contract__kof', lookup_expr='icontains')
    project_name = CharFilter(field_name='contract__quotation_obj__quick_quotation__project', lookup_expr='icontains')
    block = CharFilter(field_name='contract__quotation_obj__quick_quotation__block', lookup_expr='icontains')
    unit = CharFilter(field_name='contract__quotation_obj__quick_quotation__unit', lookup_expr='icontains')
    vade = CharFilter(field_name='vade', lookup_expr='icontains')
    leasing_rate = CharFilter(field_name='leasing_rate', lookup_expr='icontains')
    vat = CharFilter(field_name='vat', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    lease_status = CharFilter(field_name='lease_status', lookup_expr='icontains')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    leaseflex_automation = CharFilter(method = 'filter_leaseflex_automation')
    overdue = CharFilter(method = 'filter_overdue')
    item = CharFilter(method = 'filter_item')

    class Meta:
        model = Lease
        fields = ['uuid','code','contract','partner','activation_date','quotation','kof','project_name','block','unit','vade','leasing_rate','vat','currency','lease_status']
    
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
            return queryset.filter(overdue_amount__gt=0,is_last_project=True)
        else:
            return queryset.filter()
        
    def filter_item(self, queryset, item, value):
        print(value)
        if value == 'all':
            return queryset
        return queryset.filter(item__uuid = value)

class TitleDeedConfirm2Filter(FilterSet):
    name = CharFilter(method = 'filter_name')
    special = CharFilter(method = 'filter_special')
    barter = CharFilter(method = 'filter_barter')
    virman = CharFilter(method = 'filter_virman')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    bigger_than_100 = CharFilter(method = 'filter_bigger_than_100')
    the_project = CharFilter(method = 'filter_the_project')
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

    def filter_the_project(self, queryset, the_project, value):
        print("the_project",value)
        return queryset.filter(partner_contracts__project_obj__uuid=value) 
    
class TitleDeedConfirmFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')
    code = CharFilter(field_name='code', lookup_expr='icontains')
    contract = CharFilter(field_name='contract__code', lookup_expr='icontains')
    partner = CharFilter(field_name='contract__partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='contract__partner__tc_vkn_no', lookup_expr='icontains')
    activation_date = CharFilter(field_name='activation_date', lookup_expr='icontains')
    quotation = CharFilter(field_name='contract__quotation_obj__code', lookup_expr='icontains')
    kof = CharFilter(field_name='contract__kof', lookup_expr='icontains')
    project_name = CharFilter(field_name='contract__quotation_obj__quick_quotation__project', lookup_expr='icontains')
    block = CharFilter(field_name='contract__quotation_obj__quick_quotation__block', lookup_expr='icontains')
    unit = CharFilter(field_name='contract__quotation_obj__quick_quotation__unit', lookup_expr='icontains')
    vade = CharFilter(field_name='vade', lookup_expr='icontains')
    leasing_rate = CharFilter(field_name='leasing_rate', lookup_expr='icontains')
    vat = CharFilter(field_name='vat', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    lease_status = CharFilter(method = 'filter_lease_status')
    overdue_amount = CharFilter(method = 'filter_overdue_amount')
    leaseflex_automation = CharFilter(method = 'filter_leaseflex_automation')
    overdue = CharFilter(method = 'filter_overdue')
    item = CharFilter(method = 'filter_item')

    class Meta:
        model = Lease
        fields = ['uuid','code','contract','partner','activation_date','quotation','kof','project_name','block','unit','vade','leasing_rate','vat','currency','lease_status']
    
    def filter_lease_status(self, queryset, lease_status, value):
        if value == 'all':
            return queryset
        else:
            return queryset.filter(lease_status = value)
    
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
        
    def filter_item(self, queryset, item, value):
        print(value)
        if value == 'all':
            return queryset
        return queryset.filter(item__uuid = value)


