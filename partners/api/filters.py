from django.core.validators import EMPTY_VALUES
from django.db.models import Q,Sum,Count
from django.db.models.functions import Lower,Upper
from django.contrib.postgres.fields import ArrayField


from django_filters.rest_framework import FilterSet
from django_filters import CharFilter,DateFromToRangeFilter
from django.utils.timezone import make_aware
from django.utils import timezone

from datetime import datetime,timedelta
from decimal import Decimal

from .serializers import *

class SgkJobFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    sgk_job_id = CharFilter(field_name='sgk_job_id', lookup_expr='icontains')
    sgk_job_code = CharFilter(field_name='sgk_job_code', lookup_expr='icontains')
    description = CharFilter(field_name='description', lookup_expr='icontains')
    is_pep = CharFilter(field_name='is_pep')

    class Meta:
        model = SgkJob
        fields = ['uuid','sgk_job_id','sgk_job_code','description','is_pep']

class PartnerFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    country = CharFilter(field_name='country__name', lookup_expr='icontains')
    city = CharFilter(field_name='city__name', lookup_expr='icontains')

    class Meta:
        model = Partner
        fields = ['uuid','name','crm_code','customer_code','tc_vkn_no','is_commercial']


class PartnerNoteFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    user = CharFilter(field_name='user__get_full_name', lookup_expr='icontains')
    partner_id = CharFilter(field_name='partner__uuid', lookup_expr='iexact')
    title = CharFilter(field_name='title', lookup_expr='icontains')
    text = CharFilter(field_name='text', lookup_expr='icontains')

    class Meta:
        model = PartnerNote
        fields = ['uuid']

class PartnerFinancialProfileFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    partner_name = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc_vkn_no = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    partner_customer_code = CharFilter(field_name='partner__customer_code', lookup_expr='exact')
    partner_crm_code = CharFilter(field_name='partner__crm_code', lookup_expr='exact')
    
    class Meta:
        model = PartnerFinancialProfile
        fields = '__all__'
        filter_overrides = {
            ArrayField: {
                'filter_class': CharFilter,
                'extra': lambda _: {'lookup_expr': 'icontains'},
            },
        }

    def filter_uuid(self, queryset, uuid, value):
        return queryset.filter(uuid = value)


