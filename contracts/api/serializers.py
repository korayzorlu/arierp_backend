from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from datetime import timedelta

from contracts.models import *
from companies.models import Company,UserCompany
    
class ContractListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    contract_id = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    kof = serializers.CharField()
    quotation = serializers.SerializerMethodField()
    committe = serializers.CharField()
    credit_type = serializers.CharField()
    customer_representative = serializers.CharField()
    supplier = serializers.CharField()
    vendor = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    mkk_tesciline_gonderilecek_mi = serializers.BooleanField()
    kof_tan_sozlesmeye_aktarim_tarihi = serializers.DateTimeField()
    lop_open_date = serializers.DateTimeField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_quotation(self, obj):
        return obj.quotation_obj.code if obj.quotation_obj else ""
        
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.partner.tc_vkn_no if obj.partner else ""
    
    def get_vendor(self, obj):
        return obj.vendor.name if obj.vendor else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""

    def update(self, instance, validated_data):
        info = model_meta.get_field_info(instance)

        m2m_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)

        instance.save()

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)
        
        return instance
    
class ContractPaymentListSerializer(serializers.Serializer):
    id = serializers.CharField(source='uuid')
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    trn_id = serializers.CharField()
    trn_from_id = serializers.CharField()
    ledger_account_id = serializers.CharField()
    ledger_account_name = serializers.CharField()
    trade_account_code = serializers.CharField()
    type = serializers.CharField()
    posting_type = serializers.CharField()
    group_name = serializers.CharField()
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    date = serializers.DateField()
    due_date = serializers.DateField()
    debit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    credit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    local_debit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    local_credit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    currency = serializers.SerializerMethodField()
    exchange_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    user_name = serializers.CharField()
    description = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
class WarningNoticeListSerializer(serializers.Serializer):
    id = serializers.CharField(source='uuid')
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract_code = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField()
    document_id = serializers.CharField()
    risk_id = serializers.CharField()
    customer_id = serializers.CharField()
    debit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    daily_wages_date = serializers.DateField()
    process_start_date = serializers.DateField()
    service_date = serializers.DateField()
    official_cancellation_date = serializers.DateField()
    paid = serializers.DecimalField(max_digits=14,decimal_places=2)
    diff = serializers.DecimalField(max_digits=14,decimal_places=2)
    state = serializers.CharField()
    approval_state = serializers.CharField()
    termination_days = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract_code(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_partner_name(self, obj):
        return obj.contract.partner.name if obj.contract.partner else ""
    
    def get_termination_days(self, obj):
        return (obj.official_cancellation_date - obj.service_date).days if obj.official_cancellation_date and obj.service_date else ""