from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from finance.models import *
from companies.models import Company,UserCompany
from partners.models import Partner
    
class BankAccountListSerializer(serializers.Serializer):
    BankAccountId = serializers.CharField()
    IBAN = serializers.CharField()
    AccountNo = serializers.CharField()
    BranchCode = serializers.CharField()
    BranchName = serializers.CharField()
    FinmaksAccountType = serializers.CharField()
    Balance = serializers.CharField()
    AvailableBalance = serializers.CharField()
    OverDraft = serializers.CharField()
    CreditRisk = serializers.CharField()
    BlockedBalance = serializers.CharField()
    CreditLimit = serializers.CharField()
    Currency = serializers.CharField()
    CurrencyType = serializers.CharField()
    BankName = serializers.CharField()
    BankCode = serializers.CharField()
    BankIntegrationInfoId = serializers.CharField()
    LastReadTime = serializers.CharField()
    Status = serializers.CharField()

class BankAccountTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    bank_account_no = serializers.SerializerMethodField()
    bank_activity = serializers.SerializerMethodField()
    transaction_id = serializers.CharField()
    transaction_date = serializers.DateTimeField()
    explanation_field = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    sender_vkn = serializers.CharField()
    sender_iban = serializers.CharField()
    sender_account_name = serializers.CharField()
    receiver_vkn = serializers.CharField()
    receiver_iban = serializers.CharField()
    receipt_number = serializers.CharField()
    value_date = serializers.DateTimeField()
    transaction_type = serializers.CharField()
    bank_code = serializers.CharField()
    balance = serializers.DecimalField(max_digits=14,decimal_places=2)
    firm_id = serializers.CharField()
    firm_name = serializers.CharField()
    firm_merchantId = serializers.CharField()
    firm_externalCode = serializers.CharField()
    transaction_branch_code = serializers.CharField()
    transaction_branch_name = serializers.CharField()
    firm_code = serializers.CharField()
    debit = serializers.CharField()
    branch_code = serializers.CharField()
    transaction_external_id = serializers.CharField()
    external_id_used = serializers.CharField()
    external_bank_id = serializers.CharField()
    reference_no = serializers.CharField()
    finmaks_process_type = serializers.CharField()
    category_name = serializers.CharField()
    integration_field_value = serializers.CharField()
    transaction_status = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_bank_name(self, obj):
        return obj.bank_account.bank_name if obj.bank_account else ''
    
    def get_bank_account_no(self, obj):
        return obj.bank_account.account_no if obj.bank_account else ''
    
    def get_bank_activity(self, obj):
        bank_activity = obj.finmaks_transaction_bank_activities.all()
        if bank_activity:
            return True
        else:
            return False
        

class PartnerAdvanceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    crm_code = serializers.CharField()
    advance_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
