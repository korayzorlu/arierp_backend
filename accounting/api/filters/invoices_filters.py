
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from accounting.models import *
from users.models import User
from accounting.utils.common_utils import trial_balance_main_account_codes

class InvoiceFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    lease = CharFilter(field_name='lease__code', lookup_expr='icontains')
    invoice_no = CharFilter(field_name='invoice_no', lookup_expr='icontains')
    type = CharFilter(field_name='type', lookup_expr='icontains')
    date = CharFilter(field_name='date', lookup_expr='icontains')

    class Meta:
        model = Invoice
        fields = ['uuid']

