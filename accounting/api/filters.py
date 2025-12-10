
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from accounting.models import *
from accounting.utils.common_utils import trial_balance_main_account_codes

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
    lease_status = CharFilter(method='filter_lease_status')

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
    
    def filter_lease_status(self, queryset, lease_status, value):
        is_correct = self.data.get('is_correct')
        if value == "all" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status__in=["planlandi","aktiflestirildi","durduruldu"],
                contract_trial_balances__main_account_code__in=["392","393","378","378","278","279","150","151","278","279","390","391","978","979","980","981","936","934"]
            )
        elif value == "all" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status__in=["planlandi","aktiflestirildi","durduruldu"]
            ).exclude(
                contract_trial_balances__main_account_code__in=["392","393","378","378","278","279","150","151","278","279","390","391","978","979","980","981","936","934"]
            )
        elif value == "planlandi" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status'),
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "planlandi" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status')
            ).exclude(
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "aktiflestirildi" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status'),
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "aktiflestirildi" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status')
            ).exclude(
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "durduruldu" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = "durduruldu"
            )
        elif value == "durduruldu" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = "durduruldu"
            )
        elif value == "devredildi" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = "devredildi"
            )
        elif value == "devredildi" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = "devredildi"
            )
        elif value == "feshedildi" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = "feshedildi"
            )
        elif value == "feshedildi" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = "feshedildi"
            )
        elif value == "inactive":
            return queryset.filter(
                contract_leases__is_last_project = True
            ).exclude(
                contract_leases__lease_status__in=["planlandi","aktiflestirildi","durduruldu"]
            )
        return queryset
    
class UnderReviewFilter(FilterSet):
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