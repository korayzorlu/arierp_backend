
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from accounting.models import *

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