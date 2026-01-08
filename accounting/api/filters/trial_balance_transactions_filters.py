
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from accounting.models import *
from users.models import User
from accounting.utils.common_utils import trial_balance_main_account_codes

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


