from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from trade.models import *
from companies.models import Company,UserCompany
    
class TradeAccountListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    account_id = serializers.CharField()
    crm_id = serializers.CharField()
    crm_type = serializers.CharField()
    name = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
class TradeTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    trade_transaction_id = serializers.CharField()
    partner = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    posting_group_id = serializers.CharField()
    posting_group_name = serializers.CharField()
    description = serializers.CharField()
    document_no = serializers.CharField()
    amount_type = serializers.CharField()
    due_date = serializers.DateTimeField()
    record_date = serializers.DateTimeField()
    currency = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    local_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    exchange_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''

