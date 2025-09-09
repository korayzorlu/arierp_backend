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

class PurchasePaymentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    lease_code = CharFilter(field_name='lease__code', lookup_expr='icontains')
    contract = CharFilter(field_name='lease__contract__code', lookup_expr='icontains')
    contract_id = CharFilter(field_name='lease__contract__contract_id', lookup_expr='icontains')
    partner = CharFilter(field_name='lease__contract__partner__name', lookup_expr='icontains')
    vendor = CharFilter(field_name='lease__contract__vendor__name', lookup_expr='icontains')
    currency = CharFilter(field_name='lease__currency__code', lookup_expr='icontains')
    project = CharFilter(field_name='lease__contract__project', lookup_expr='icontains')
    status = CharFilter(field_name='lease__status__name', lookup_expr='icontains')
    lease_status = CharFilter(field_name='lease__lease_status', lookup_expr='icontains')
    status_control = CharFilter(method = 'filter_status_control') 

    class Meta:
        model = PurchasePayment
        fields = ['uuid']

    def filter_status_control(self, queryset, status_control, value):
        if value == "true":
            print( "evet var")
            return queryset.filter(
                lease__lease_status = "planlandi"
            ).annotate(
                total_purchase_document=Sum('lease__lease_purchase_documents__total_amount')
            ).filter(total_purchase_document__gt=0)
        else:
            print("hayır yok")
            return queryset.filter()
    
class PurchaseDocumentFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    lease_code = CharFilter(field_name='lease__code', lookup_expr='icontains')
    lease = CharFilter(field_name='lease__code', lookup_expr='exact')
    contract = CharFilter(field_name='lease__contract__code', lookup_expr='icontains')
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    vendor = CharFilter(field_name='vendor__name', lookup_expr='icontains')
    document_number = CharFilter(field_name='document_number', lookup_expr='icontains')

    class Meta:
        model = PurchaseDocument
        fields = ['uuid']