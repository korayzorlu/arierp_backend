
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from accounting.models import *
from users.models import User
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
    transfer_count = CharFilter(method='filter_transfer_count')

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
    
    def filter_transfer_count(self, queryset, transfer_count, value):
        print(transfer_count)
    
    def filter_lease_status(self, queryset, lease_status, value):
        is_correct = self.data.get('is_correct')
        if value == "all" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                #contract_leases__lease_status__in=["planlandi","aktiflestirildi","durduruldu"]
            )
        elif value == "all" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status__in=["planlandi","aktiflestirildi"]
            ).exclude(
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes({'lease_status': 'aktiflestirildi'}) + trial_balance_main_account_codes({'lease_status': 'planlandi'})
            )
        elif value == "planlandi" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status'),
                contract_leases__currency__code = self.data.get('currency'),
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "planlandi" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status'),
                contract_leases__currency__code = self.data.get('currency'),
            ).exclude(
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "aktiflestirildi" and is_correct == "true":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status'),
                contract_leases__currency__code = self.data.get('currency'),
                contract_trial_balances__main_account_code__in=trial_balance_main_account_codes(self.data)
            )
        elif value == "aktiflestirildi" and is_correct == "false":
            return queryset.filter(
                contract_leases__is_last_project = True,
                contract_leases__lease_status = self.data.get('lease_status'),
                contract_leases__currency__code = self.data.get('currency'),
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

class TrialBalanceTransactionFilter(FilterSet):
    trial_balance = CharFilter(field_name='trial_balance__account_code', lookup_expr='icontains')
    tb_uuid = CharFilter(field_name='trial_balance__uuid', lookup_expr='exact')
    account_name = CharFilter(field_name='trial_balance__account_name', lookup_expr='icontains')
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='icontains')
    ledger_period = CharFilter(field_name='ledger_period', lookup_expr='icontains')
    transaction_text = CharFilter(field_name='transaction_text', lookup_expr='icontains')
    amount_type = CharFilter(field_name='amount_type', lookup_expr='icontains')
    transaction_date = CharFilter(field_name='transaction_date', lookup_expr='icontains')
    main_account_code = CharFilter(method = 'filter_main_account_code')
    user = CharFilter(method = 'filter_user')

    class Meta:
        model = TrialBalanceTransaction
        fields = ['uuid']

    def filter_main_account_code(self, queryset, main_account_code, value):
        if value == 'all':
            return queryset
        return queryset.filter(trial_balance__main_account_code = value)
    
    def filter_user(self, queryset, user, value):
        user_objs = User.objects.filter(name__icontains=value)
        user_ids = [u.leaseflex_id for u in user_objs if u.leaseflex_id]
        if not user_objs and not user_ids:
            return queryset
        return queryset.filter(user_id__in=user_ids)


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