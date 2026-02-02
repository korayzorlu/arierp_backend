from rest_framework import serializers

from accounting.models import *
from leasing.models import Lease

class InvoiceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    trn_id = serializers.CharField()
    invoice_no = serializers.CharField()
    type = serializers.CharField()
    date = serializers.DateTimeField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    currency = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else '',

    def get_currency(self, obj):
        return obj.lease.currency.code if obj.lease and obj.lease.currency else ''