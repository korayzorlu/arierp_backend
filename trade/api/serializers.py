from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.utils.timezone import localtime

from decimal import Decimal

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

class TradeTransaction1ListSerializer(serializers.Serializer):
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
        return localtime(obj.due_date).date().strftime('%d.%m.%Y') if obj.due_date else ''

    def get_balances(self, obj):
        objs = TradeTransaction.objects.select_related().filter(lease = obj.lease).exclude(delete_status__in=['2']).order_by('posting_group_id','due_date','record_date','trade_transaction_id')
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
    
class TradeTransactionForCustomerInLeaseListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    trade_transaction_id = serializers.CharField()
    partner = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    posting_group_id = serializers.CharField()
    posting_group_name = serializers.CharField()
    description = serializers.SerializerMethodField()
    document_no = serializers.CharField()
    amount_type = serializers.CharField()
    due_date = serializers.SerializerMethodField()
    record_date = serializers.DateTimeField()
    currency = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    local_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    exchange_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    applied = serializers.SerializerMethodField()
    balances = serializers.SerializerMethodField()
    apply_status = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ''
    
    def get_description(self, obj):
        if "Kira Ödemeleri" in obj.description:
            installment = obj.lease.lease_installments.filter(payment_date=obj.due_date).first()
            if installment.type == "2":
                first_word = "Peşinat"
            elif installment.type == "5":
                first_word = "Devir Bedeli"
            else:
                first_word = f"{installment.sequency}. Kira"

            months = {
                1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
            }
            month_num = localtime(obj.due_date).date().month
            year = localtime(obj.due_date).date().year

            return f"{first_word} Taksiti Vadesi"
        return obj.description if obj.description else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''
    
    def get_due_date(self, obj):
        return localtime(obj.due_date).date().strftime('%d.%m.%Y') if obj.due_date else ''

    def get_applied(self, obj):
        objs = TradeTransaction.objects.select_related().filter(lease = obj.lease).exclude(delete_status__in=['2']).order_by('due_date','-posting_group_id')
        prev_balance = Decimal('0.00')
        applied = Decimal('0.00')
        group = ""
        for o in objs:
            if group != "" and group != o.posting_group_id:
                prev_balance = Decimal('0.00')
            current_amount = o.amount if o.amount_type == '1' else -o.amount
            prev_balance += current_amount
            if o.id == obj.id:
                balance = prev_balance
            if o.id != obj.id and obj.amount_type == '1' and o.amount_type == '0' and o.due_date >= obj.due_date:
                applied += current_amount
                return applied
            group = o.posting_group_id

    def get_balances(self, obj):
        objs = TradeTransaction.objects.select_related().filter(lease = obj.lease).exclude(delete_status__in=['2']).order_by('posting_group_id','due_date','record_date','trade_transaction_id')
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

    def get_apply_status(self, obj):
        objs = TradeTransaction.objects.select_related().filter(lease = obj.lease).exclude(delete_status__in=['2']).order_by('posting_group_id','due_date','record_date','trade_transaction_id')
        prev_balance = 0
        group = ""
        is_applied = False
        for o in objs:
            if group != "" and group != o.posting_group_id:
                prev_balance = 0
                is_applied = False
            current_amount = o.amount if o.amount_type == '1' else -o.amount
            prev_balance += current_amount
            if o.id == obj.id:
                balance = prev_balance
                if balance <= 0:
                    is_applied = True
            if o.id != obj.id and obj.amount_type == '1' and o.amount_type == '0' and o.due_date >= obj.due_date:
                if prev_balance <= 0:
                    is_applied = True
            group = o.posting_group_id

        if obj.amount_type == "0":
            return ""
        return "İşlendi" if is_applied else "İşlenmedi"