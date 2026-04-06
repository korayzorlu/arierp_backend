from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter
from django.db.models.functions import Lower,Upper
from django.db.models import Q,Sum

from  leasing.models import Lease

class LeaseFilterMixin(FilterSet):
    code = CharFilter(field_name='code', lookup_expr='icontains')
    contract = CharFilter(field_name='contract__code', lookup_expr='exact')
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
        fields = '__all__'
    
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
            return queryset.filter((Q(overdue_amount__gt=0)|Q(overdue_days__gt=0))&Q(is_last_project=True))
        else:
            return queryset.filter()
        
    def filter_item(self, queryset, item, value):
        if value == 'all':
            return queryset
        return queryset.filter(item__uuid = value)
