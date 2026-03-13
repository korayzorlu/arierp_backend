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
from partners.models import Partner

class BlackListPersonFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    tc_vkn_passport_no = CharFilter(field_name='tc_vkn_passport_no', lookup_expr='icontains')
    other_names = CharFilter(field_name='other_names', lookup_expr='icontains')
    nationality = CharFilter(field_name='nationality', lookup_expr='icontains')
    birthday = CharFilter(field_name='birthday', lookup_expr='icontains')
    organization = CharFilter(field_name='organization', lookup_expr='icontains')
    date_number = CharFilter(field_name='date_number', lookup_expr='icontains')

    class Meta:
        model = BlackListPerson
        fields = ['uuid']

class ScanPartnerFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    tc_vkn_no = CharFilter(field_name='tc_vkn_no', lookup_expr='icontains')
    crm_code = CharFilter(field_name='crm_code', lookup_expr='exact')

    class Meta:
        model = Partner
        fields = ['uuid']

class PepPartnerFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    tc_vkn_no = CharFilter(field_name='tc_vkn_no', lookup_expr='icontains')
    crm_code = CharFilter(field_name='crm_code', lookup_expr='exact')
    birthday = CharFilter(field_name='birthday', lookup_expr='icontains')
    sgk_job_code = CharFilter(field_name='sgk_job_code', lookup_expr='icontains')
    is_pep = CharFilter(method='filter_is_pep')
    pep_degree = CharFilter(field_name='pep_degree', lookup_expr='exact')
    pep_description = CharFilter(field_name='pep_description', lookup_expr='icontains')

    class Meta:
        model = Partner
        fields = ['uuid']

    def filter_is_pep(self, queryset, is_pep, value):
        if value == "all":
            return queryset
        elif value.lower() == 'true':
            return queryset.filter(is_pep = True)
        elif value.lower() == 'false':
            return queryset.filter(is_pep = False)
        else:
            return queryset

class ThirdPersonFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    name = CharFilter(method='filter_name')
    tc_vkn_no = CharFilter(field_name='tc_vkn_no', lookup_expr='icontains')
    status = CharFilter(method='filter_status')
    is_email_sent = CharFilter(method='filter_is_email_sent')

    class Meta:
        model = ThirdPerson
        fields = ['uuid','name','tc_vkn_no','status','is_email_sent']

    def filter_name(self, queryset, name, value):
        return queryset.annotate(lowercase=Lower('name'),uppercase=Upper('name')).filter(Q(lowercase__icontains = value) | Q(uppercase__icontains = value))

    def filter_status(self, queryset, status, value):
        if value == "all":
            return queryset
        return queryset.filter(status = value)
    
    def filter_is_email_sent(self, queryset, is_email_sent, value):
        if value == "all":
            return queryset
        elif value.lower() == 'true':
            return queryset.filter(is_email_sent = True)
        elif value.lower() == 'false':
            return queryset.filter(is_email_sent = False)
        else:
            return queryset