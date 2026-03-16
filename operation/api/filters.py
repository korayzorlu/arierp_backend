from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter


from .serializers import *

class ContractInSupplierFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    quotation = CharFilter(field_name='quotation_obj__code', lookup_expr='exact')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['uuid','code','contract_id','project','customer_representative']

class ContractInProcessFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    quotation = CharFilter(field_name='quotation_obj__code', lookup_expr='exact')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['uuid','code','contract_id','project','customer_representative']

class ContractInArchiveFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    quotation = CharFilter(field_name='quotation_obj__code', lookup_expr='exact')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['uuid','code','contract_id','project','customer_representative']

class PartnerAdvanceActivityFilter(FilterSet):
    created_date = DateFromToRangeFilter(field_name = 'created_date')
    class Meta:
        model = PartnerAdvanceActivity
        fields = ['uuid','bank','bank_account_no','process_type','receipt_no','description','created_date']

class PartnerAdvanceActivityLeaseFilter(FilterSet):
    bank_activity = CharFilter(method = 'filter_bank_activity')
    lease = CharFilter(method = 'filter_lease')
    class Meta:
        model = PartnerAdvanceActivityLease
        fields = ['uuid','bank_activity','lease']

    def filter_bank_activity(self, queryset, bank_activity, value):
        return queryset.filter(bank_activity__uuid = value)
    
    def filter_lease(self, queryset, lease, value):
        return queryset.filter(lease__lease = value)
    
class TitleDeedInvoiceControlFilter(FilterSet):
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
    invoices = CharFilter(method = 'filter_invoices')
    purchase_documents = CharFilter(method = 'filter_purchase_documents')

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
        if value == 'all':
            return queryset
        return queryset.filter(item__uuid = value)
    
    def filter_invoices(self, queryset, invoices, value):
        if value == 'all':
            return queryset
        elif value == 'kesildi':
            return queryset.annotate(lease_invoices_count=Count('lease_invoices', distinct=True),).filter(lease_invoices_count__gt=0)
        elif value == 'fatura_yok':
            return queryset.annotate(lease_invoices_count=Count('lease_invoices', distinct=True),).filter(lease_invoices_count=0)
        else:
            return queryset
        
    def filter_purchase_documents(self, queryset, purchase_documents, value):
        if value == 'all':
            return queryset
        elif value == 'kesildi':
            return queryset.annotate(purchase_documents_count=Count('lease_purchase_documents', distinct=True),).filter(purchase_documents_count__gt=0)
        elif value == 'fatura_yok':
            return queryset.annotate(purchase_documents_count=Count('lease_purchase_documents', distinct=True),).filter(purchase_documents_count=0)
        else:
            return queryset

class UntitleDeedLeaseFilter(FilterSet):
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
    invoices = CharFilter(method = 'filter_invoices')
    purchase_documents = CharFilter(method = 'filter_purchase_documents')

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
    
    def filter_invoices(self, queryset, invoices, value):
        if value == 'all':
            return queryset
        elif value == 'kesildi':
            return queryset.annotate(lease_invoices_count=Count('lease_invoices', distinct=True),).filter(lease_invoices_count__gt=0)
        elif value == 'fatura_yok':
            return queryset.annotate(lease_invoices_count=Count('lease_invoices', distinct=True),).filter(lease_invoices_count=0)
        else:
            return queryset
        
    def filter_purchase_documents(self, queryset, purchase_documents, value):
        if value == 'all':
            return queryset
        elif value == 'kesildi':
            return queryset.annotate(purchase_documents_count=Count('lease_purchase_documents', distinct=True),).filter(purchase_documents_count__gt=0)
        elif value == 'fatura_yok':
            return queryset.annotate(purchase_documents_count=Count('lease_purchase_documents', distinct=True),).filter(purchase_documents_count=0)
        else:
            return queryset