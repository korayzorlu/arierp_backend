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
    due_date = serializers.SerializerMethodField()
    record_date = serializers.DateTimeField()
    currency = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    local_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    exchange_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    balances = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''
    
    def get_due_date(self, obj):
        return obj.due_date.date() if obj.due_date else ''

    def get_balances(self, obj):
        objs = TradeTransaction.objects.filter(lease = obj.lease).order_by('posting_group_id','due_date','record_date','trade_transaction_id')
        prev_balance = 0
        prev_tl_balance = 0
        group = ""
        for o in objs:
            if group != "" and group != o.posting_group_id:
                prev_balance = 0
                prev_tl_balance = 0
            current_amount = o.amount if o.amount_type == '1' else -o.amount
            current_local_amount = o.local_amount if o.amount_type == '1' else -o.local_amount
            prev_balance += current_amount
            prev_tl_balance += current_local_amount
            if o.id == obj.id:
                return {
                    "balance": prev_balance,
                    "tl_balance": prev_tl_balance
                }
            group = o.posting_group_id

