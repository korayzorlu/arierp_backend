from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum,F,IntegerField
from django.db.models.functions import Lower,Upper,Abs,Cast
from django.utils.dateparse import parse_datetime, parse_date

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class KapamaDetayFilter(FilterSet):
    contract = CharFilter(method = 'filter_contract')
    odeme_tarihi = CharFilter(method = 'filter_odeme_tarihi')
    fatura_tarihi = CharFilter(method = 'filter_fatura_tarihi')

    class Meta:
        model = KapamaDetay
        fields = '__all__'

    def filter_contract(self, queryset, contract, value):
        return queryset.filter(contract_header_id__in=Contract.objects.filter(code__icontains=value).values_list(Cast('contract_id', IntegerField()), flat=True))

    def filter_odeme_tarihi(self, queryset, odeme_tarihi, value):
        parsed = parse_datetime(value)
        if parsed:
            return queryset.filter(odeme_tarihi=parsed.date())
        date_parsed = parse_date(value)
        if date_parsed:
            return queryset.filter(odeme_tarihi=date_parsed)
        return queryset
    
    def filter_fatura_tarihi(self, queryset, fatura_tarihi, value):
        parsed = parse_datetime(value)
        if parsed:
            return queryset.filter(fatura_tarihi=parsed.date())
        date_parsed = parse_date(value)
        if date_parsed:
            return queryset.filter(fatura_tarihi=date_parsed)
        return queryset

class KapamaHareketiFilter(FilterSet):
    contract = CharFilter(method = 'filter_contract')
    tarih = CharFilter(method = 'filter_tarih')

    class Meta:
        model = KapamaHareketi
        fields = '__all__'

    def filter_contract(self, queryset, contract, value):
        return queryset.filter(contract_header_id__in=Contract.objects.filter(code__icontains=value).values_list(Cast('contract_id', IntegerField()), flat=True))

    def filter_tarih(self, queryset, tarih, value):
        parsed = parse_datetime(value)
        if parsed:
            return queryset.filter(tarih=parsed.date())
        date_parsed = parse_date(value)
        if date_parsed:
            return queryset.filter(tarih=date_parsed)
        return queryset
    
class KrsReportFilter(FilterSet):
    code = CharFilter(field_name='contract__code', lookup_expr='icontains')
    hesap_numarasi = CharFilter(field_name='hesap_numarasi', lookup_expr='icontains')

    class Meta:
        model = KrsReport
        fields = '__all__'