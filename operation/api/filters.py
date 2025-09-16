from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.db.models.functions import Lower,Upper

from django_filters.rest_framework import FilterSet
from django_filters import CharFilter

from .serializers import *

class ContractInSupplierFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_tc = CharFilter(field_name='partner__tc_vkn_no', lookup_expr='icontains')
    quotation = CharFilter(field_name='quotation_obj__code', lookup_expr='exact')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')

    class Meta:
        model = Contract
        fields = ['uuid','code','contract_id','project','customer_representative']