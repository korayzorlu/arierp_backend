from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum,F
from django.db.models.functions import Lower, Upper, Abs
from django.utils.dateparse import parse_datetime, parse_date

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter


from .serializers import *
from leasing.api.filters import LeaseFilter

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
    
class TitleDeedInvoiceControlFilter(LeaseFilter):
    invoices = CharFilter(method = 'filter_invoices')
    purchase_documents = CharFilter(method = 'filter_purchase_documents')
    ari_bbsn_warning = CharFilter(method = 'filter_ari_bbsn_warning')
    activation_date = CharFilter(method = 'filter_activation_date')

    class Meta:
        model = Lease
        fields = '__all__'
    
    def filter_invoices(self, queryset, invoices, value):
        if value == 'all':
            return queryset
        main_lease_ids_with_docs = Lease.objects.filter(
            lease_invoices__isnull=False
        ).values_list('main_lease_id', flat=True).distinct()
        if value == 'kesildi':
            return queryset.filter(main_lease_id__in=main_lease_ids_with_docs)
        elif value == 'fatura_yok':
            return queryset.exclude(main_lease_id__in=main_lease_ids_with_docs)
        else:
            return queryset
        
    def filter_purchase_documents(self, queryset, purchase_documents, value):
        if value == 'all':
            return queryset
        main_lease_ids_with_docs = Lease.objects.filter(
            lease_purchase_documents__isnull=False
        ).values_list('main_lease_id', flat=True).distinct()
        if value == 'kesildi':
            return queryset.filter(main_lease_id__in=main_lease_ids_with_docs)
        elif value == 'fatura_yok':
            return queryset.exclude(main_lease_id__in=main_lease_ids_with_docs)
        else:
            return queryset
        
    def filter_ari_bbsn_warning(self, queryset, ari_bbsn_warning, value):
        if value == 'true':
            return queryset.filter(
                (
                    Q(ari_bbsn__isnull=True) |
                    Q(ari_bbsn='')
                ) |
                (
                    ~Q(ari_bbsn=F('crm_bbsn')) &
                    Q(crm_bbsn__isnull=False) &
                    ~Q(crm_bbsn='')
                )
            )
        else:
            return queryset
        
    def filter_activation_date(self, queryset, activation_date, value):
        parsed = parse_datetime(value)
        if parsed:
            return queryset.filter(activation_date=parsed.date())
        date_parsed = parse_date(value)
        if date_parsed:
            return queryset.filter(activation_date=date_parsed)
        return queryset


class UntitleDeedLeaseFilter(LeaseFilter):
    invoices = CharFilter(method = 'filter_invoices')
    purchase_documents = CharFilter(method = 'filter_purchase_documents')
    class Meta:
        model = Lease
        fields = '__all__'
    
    def filter_invoicessss(self, queryset, invoices, value):
        if value == 'all':
            return queryset
        elif value == 'kesildi':
            return queryset.annotate(lease_invoices_count=Count('lease_invoices', distinct=True),).filter(lease_invoices_count__gt=0)
        elif value == 'fatura_yok':
            return queryset.annotate(lease_invoices_count=Count('lease_invoices', distinct=True),).filter(lease_invoices_count=0)
        else:
            return queryset
        
    def filter_invoices(self, queryset, invoices, value):
        if value == 'all':
            return queryset
        main_lease_ids_with_docs = Lease.objects.filter(
            lease_invoices__isnull=False
        ).values_list('main_lease_id', flat=True).distinct()
        if value == 'kesildi':
            return queryset.filter(main_lease_id__in=main_lease_ids_with_docs)
        elif value == 'fatura_yok':
            return queryset.exclude(main_lease_id__in=main_lease_ids_with_docs)
        else:
            return queryset
        
    def filter_purchase_documents(self, queryset, purchase_documents, value):
        if value == 'all':
            return queryset
        main_lease_ids_with_docs = Lease.objects.filter(
            lease_purchase_documents__isnull=False
        ).values_list('main_lease_id', flat=True).distinct()
        if value == 'kesildi':
            return queryset.filter(main_lease_id__in=main_lease_ids_with_docs)
        elif value == 'fatura_yok':
            return queryset.exclude(main_lease_id__in=main_lease_ids_with_docs)
        else:
            return queryset
 
class KepMonitoringFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    customerCode = CharFilter(method = 'filter_customer_code')
    customer_type = CharFilter(method = 'filter_customer_type')
    crmCode = CharFilter(method = 'filter_crm_code')
    tcVknNo = CharFilter(method = 'filter_tc_vkn_no')
    types = CharFilter(method = 'filter_types')
    name = CharFilter(method = 'filter_name')
    country_name = CharFilter(method = 'filter_country')
    kep = CharFilter(field_name = 'kep', lookup_expr = 'contains')
    is_turkkep = CharFilter(method='filter_is_turkkep')
    has_kep = CharFilter(method='filter_has_kep')
    last_contract_code = CharFilter(field_name='partner_contracts__contract_leases__contract__code', lookup_expr='exact')
    last_contract_date = CharFilter(method='filter_last_contract_date')
    class Meta:
        model = Partner
        fields = ['uuid','types','name','crm_code','customer_code','customer_type','is_commercial','tc_vkn_no']

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)
    
    def filter_customer_code(self, queryset, customer_code, value):
        return queryset.filter(customer_code = value)

    def filter_crm_code(self, queryset, crm_code, value):
        return queryset.filter(crm_code = value)
    
    def filter_tc_vkn_no(self, queryset, tc_vkn_no, value):
        return queryset.filter(tc_vkn_no = value)
    
    def filter_types(self, queryset, types, value):
        return queryset.filter(types__overlap = value)
    
    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
    def filter_country(self, queryset, country, value):
        return queryset.annotate(lowercase=Lower('country__name'),uppercase=Upper('country__name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))
    
    def filter_customer_type(self, queryset, customer_type, value):
        return queryset.filter(customer_type = value)
    
    def filter_is_turkkep(self, queryset, is_turkkep, value):
        if value == "true":
            value = True
        elif value == "false":
            value = False
        elif value == "all":
            return queryset
        return queryset.filter(is_turkkep = value)

    def filter_has_kep(self, queryset, has_kep, value):
        if value == "true":
            value = True
        elif value == "false":
            value = False
        elif value == "all":
            return queryset
        return queryset.filter(kep__isnull = not value)   

    def filter_last_contract_date(self, queryset, last_contract_date, value):
        parsed = parse_datetime(value)
        if parsed:
            return queryset.filter(partner_contracts__contract_leases__activation_date=parsed.date())
        date_parsed = parse_date(value)
        if date_parsed:
            return queryset.filter(partner_contracts__contract_leases__activation_date=date_parsed)
        return queryset 
    
    def filter_last_lease_status(self, queryset, lease_status, value):
        if value == 'all':
            return queryset
        if value != 'all':
            return queryset.filter(partner_contracts__contract_leases__lease_status=value)
        else:
            return queryset






















