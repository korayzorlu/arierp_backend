from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class PartnerAdvanceFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    tc_vkn_no = CharFilter(field_name='tc_vkn_no', lookup_expr='exact')
    crm_code = CharFilter(field_name='crm_code', lookup_expr='exact')

    class Meta:
        model = Partner
        fields = ['uuid']

class BankAccountFilter(FilterSet):
    bank_account_id = CharFilter(field_name='bank_account_id', lookup_expr='icontains')
    iban = CharFilter(field_name='iban', lookup_expr='icontains')
    account_no = CharFilter(field_name='account_no', lookup_expr='icontains')
    branch_code = CharFilter(field_name='branch_code', lookup_expr='icontains')
    branch_name = CharFilter(field_name='branch_name', lookup_expr='icontains')
    finmaks_account_type = CharFilter(field_name='finmaks_account_type', lookup_expr='icontains')
    currency = CharFilter(field_name='currency__code', lookup_expr='icontains')
    currency_type = CharFilter(field_name='currency_type', lookup_expr='icontains')
    bank_name = CharFilter(field_name='bank_name', lookup_expr='icontains')
    bank_code = CharFilter(field_name='bank_code', lookup_expr='icontains')
    bank_integration_info_id = CharFilter(field_name='bank_integration_info_id', lookup_expr='icontains')
    last_read_time = CharFilter(field_name='last_read_time', lookup_expr='icontains')
    status = CharFilter(field_name='status', lookup_expr='icontains')
    finekra_bank_account_id = CharFilter(field_name='finekra_bank_account_id', lookup_expr='icontains')
    is_active = CharFilter(method='filter_is_active')
    class Meta:
        model = FinmaksBankAccount
        fields = ['uuid']

    def filter_is_active(self, queryset, is_active, value):
        if value == 'true':
            return queryset.filter(is_active=True)
        elif value == 'false':
            return queryset.filter(is_active=False)
        return queryset

class BankAccountTransactionFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    class Meta:
        model = FinmaksTransaction
        fields = ['uuid']

class BankAccountTransactionFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')
    transaction_date = CharFilter(method='filter_transaction_date')
    transaction_id = CharFilter(field_name='transaction_id', lookup_expr='icontains')
    explanation_field = CharFilter(field_name='explanation_field', lookup_expr='icontains')
    bank_name = CharFilter(field_name='bank_account__bank_name', lookup_expr='icontains')
    bank_account_no = CharFilter(field_name='bank_account__account_no', lookup_expr='icontains')

    class Meta:
        model = FinmaksTransaction
        fields = ['uuid']

    def filter_transaction_date_old(self, queryset, transaction_date, value):
        if not value:
            return queryset
        # Tarih parçalarını ayır (örn: "05.11.2025", "05.11.", "05")
        parts = value.split('.')
        q = Q()
        if len(parts) > 0 and parts[0]:
            # Gün filtresi
            q &= Q(transaction_date__day=parts[0])
        if len(parts) > 1 and parts[1]:
            # Ay filtresi
            q &= Q(transaction_date__month=parts[1])
        if len(parts) > 2 and parts[2]:
            # Yıl filtresi
            q &= Q(transaction_date__year=parts[2])
        return queryset.filter(q)
    
    def filter_transaction_date(self, queryset, transaction_date, value):
        if not value:
            return queryset

        # ISO format (2026-04-28T00:00:00.000Z) veya düz tarih (dd.mm.yyyy) destekle
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            # UTC datetime'ı lokal timezone'a çevir, sonra tarihi al
            local_dt = timezone.localtime(dt)
            date_obj = local_dt.date()
        except ValueError:
            date_obj = datetime.strptime(value, '%d.%m.%Y').date()

        return queryset.filter(transaction_date__date=date_obj)


class VPosTransactionFilter(FilterSet):
    uuid = CharFilter(field_name='uuid', lookup_expr='exact')

    class Meta:
        model = VPosTransaction
        fields = ['uuid']


