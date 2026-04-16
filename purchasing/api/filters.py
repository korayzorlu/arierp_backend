from django.core.validators import EMPTY_VALUES
from django.db.models import Q, Sum, F, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
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
    kdv = CharFilter(method = 'filter_kdv')
    special = CharFilter(method = 'filter_special')

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
        
    def filter_kdv(self, queryset, kdv, value):
        if value == "true":
            
            return queryset.filter(
                Q(lease__lease_installments__payment_date__gte=date(2023, 7, 10)) &
                (
                    Q(lease__vat=Decimal('18.00')) |
                    Q(lease__vat=Decimal('8.00'))
                ) &
                Q(lease__is_last_project=True)
            )
        else:
            return queryset.filter()
        
    def filter_special(self, queryset, special, value):
        queryset = self.Meta.model.objects.filter()
        if value == "true":
            queryset = queryset.filter(
                Q(lease__contract__partner__types__contains=['special']) |
                Q(lease__contract__partner__crm_code__in=["23371", "9341", "10495", "4305", "10437", "4441", "11722", "24120"])
            )

        else:
            queryset = queryset.filter(
                ~Q(lease__contract__partner__types__contains=['special']) &
                ~Q(lease__contract__partner__crm_code__in=["23371", "9341", "10495", "4305", "10437", "4441", "11722", "24120"]) 
            )
        return queryset
        
    
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

class PurchaseDocumentItemFilter(FilterSet):
    uuid = CharFilter(method = 'filter_uuid')
    document_line_id = CharFilter(field_name='document_line_id', lookup_expr='icontains')
    purchase_document = CharFilter(field_name='purchase_document__code', lookup_expr='icontains')
    stock_name = CharFilter(field_name='stock_name', lookup_expr='icontains')
    description = CharFilter(field_name='description', lookup_expr='icontains')
    crm_satici = CharFilter(field_name='lease__crm_satici', lookup_expr='icontains')
    is_agreement = CharFilter(method='filter_is_agreement')

    class Meta:
        model = PurchaseDocumentItem
        fields = ['uuid']

    def filter_is_agreement(self, queryset, _name, value):
        if value == 'all':
            return queryset

        agreement_expr = ExpressionWrapper(
            F('total_amount') - Coalesce(F('lease__crm_invoice_total_amount'), Value(Decimal('0.00'))),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        queryset = queryset.annotate(agreement_amount=agreement_expr)

        if value == 'var':
            return queryset.filter(agreement_amount__gt=-1000, agreement_amount__lt=1000)
        elif value == 'yok':
            return queryset.exclude(agreement_amount__gt=-1000, agreement_amount__lt=1000)
        else:
            return queryset