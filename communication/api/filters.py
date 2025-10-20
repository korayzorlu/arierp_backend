
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters import CharFilter

from communication.models import *

    
class SMSFilter(FilterSet):
    partner = CharFilter(field_name='partner__name', lookup_expr='icontains')
    partner_id = CharFilter(field_name='partner__uuid', lookup_expr='exact')
    phone_number = CharFilter(field_name='phone_number', lookup_expr='icontains')

    class Meta:
        model = SMS
        fields = ['uuid','packet_id','message_id','reference_id','send_date','delivery_date']