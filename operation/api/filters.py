from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum,F
from django.db.models.functions import Lower,Upper
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
    is_agreement = CharFilter(method = 'filter_is_agreement')

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
    
    def filter_is_agreement(self, queryset, is_agreement, value):
        if value == 'all':
            return queryset
        
        main_lease_ids = list(queryset.values_list('main_lease_id', flat=True).distinct())
        
        pd_totals_by_main = {}
        related_leases = Lease.objects.filter(
            main_lease_id__in=main_lease_ids
        ).prefetch_related('lease_purchase_documents')

        for lease in related_leases:
            mid = lease.main_lease_id
            if mid not in pd_totals_by_main:
                pd_totals_by_main[mid] = Decimal('0.00')
            for pd in lease.lease_purchase_documents.all():
                pd_totals_by_main[mid] += pd.total_amount

        var_uuids, yok_uuids = set(), set()
        for lease in queryset:
            pd_total = pd_totals_by_main.get(lease.main_lease_id, Decimal('0.00'))
            agreement_amount = pd_total - (lease.crm_invoice_total_amount or Decimal('0.00'))
            if -1000 < agreement_amount < 1000:
                var_uuids.add(lease.uuid)
            else:
                yok_uuids.add(lease.uuid)
        
        if value == 'var':
            return queryset.filter(uuid__in=var_uuids)
        elif value == 'yok':
            return queryset.filter(uuid__in=yok_uuids)
        else:
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