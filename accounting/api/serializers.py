from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from accounting.models import *

class AccountListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    #accounts = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    balance = serializers.DecimalField(max_digits=14,decimal_places=2)
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_partner(self, obj):
        return {"uuid":obj.partner.uuid,"name":obj.partner.name} if obj.partner else {}
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''
    
    def get_type(self, obj):
        return obj.type.code if obj.type else ''
    
    def get_accounts(self, obj):
        account_list = []
        accounts = Account.objects.select_related("currency","partner").filter(partner = obj.partner)
        for account in accounts:
            account_list.append({
                "uuid" : account.uuid,
                "partner" : account.partner.name,
                "currency" : account.currency.code,
                "balance" : account.balance
            })
        return account_list
    
    # def get_type(self, obj):
    #     return obj.get_type_display()

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
    
class TransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    account = serializers.SerializerMethodField()
    accountPartner = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    date = serializers.DateTimeField()
    type = serializers.CharField()
    ref_uuid = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    description = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_account(self, obj):
        return obj.account.uuid if obj.account else ''

    def get_accountPartner(self, obj):
        return obj.account.partner.name if obj.account.partner else ''
    
    def get_currency(self, obj):
        return obj.account.currency.code if obj.account.currency else ''

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
     
class InvoiceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    invoice_no = serializers.CharField()
    type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    date = serializers.DateTimeField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_partner(self, obj):
        return {"uuid":obj.partner.uuid,"name":obj.partner.name} if obj.partner else {}
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''

class PaymentListSerializer(serializers.Serializer):
        uuid = serializers.CharField()
        companyId = serializers.SerializerMethodField()
        partner = serializers.SerializerMethodField()
        currency = serializers.SerializerMethodField()
        payment_no = serializers.CharField()
        type = serializers.CharField()
        receiver = serializers.SerializerMethodField()
        amount = serializers.DecimalField(max_digits=14,decimal_places=2)
        date = serializers.DateTimeField()
        
        def get_companyId(self, obj):
            return obj.company.id if obj.company else ''

        def get_partner(self, obj):
            return {"uuid":obj.partner.uuid,"name":obj.partner.name} if obj.partner else {}
        
        def get_currency(self, obj):
            return obj.currency.code if obj.currency else ''
        
        def get_receiver(self, obj):
            return obj.get_receiver_display() if obj.receiver else ''
        
class TrialBalanceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    account_id = serializers.CharField()
    main_account_code = serializers.CharField()
    main_account_code_list = serializers.SerializerMethodField()
    account_code = serializers.CharField()
    account_code_trim = serializers.CharField()
    account_name = serializers.CharField()
    balance_account_type = serializers.CharField()
    balance_debit = serializers.DecimalField(max_digits=14,decimal_places=2)
    balance_credit = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_debit = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_credit = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_tl = serializers.SerializerMethodField()
    balance_debit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    balance_credit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_debit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_credit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_currency = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''

    def get_total_tl(self, obj):
        return obj.balance_debit - obj.balance_credit

    def get_total_currency(self, obj):
        return obj.balance_debit_alternate - obj.balance_credit_alternate
    
    def get_main_account_code_list(self, obj):
        main_account_codes = TrialBalance.objects.values_list('main_account_code', flat=True).distinct()

        return main_account_codes
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ''
    
class TrialBalanceContractListSerializer(serializers.Serializer):
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
    created_date_leaseflex = serializers.DateTimeField()
    is_commercial = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_quotation(self, obj):
        return obj.quotation_obj.code if obj.quotation_obj else ""
        
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_is_commercial(self, obj):
        return obj.partner.is_commercial if obj.partner else False
    
    def get_partner_tc(self, obj):
        return obj.partner.tc_vkn_no if obj.partner else ""
    
    def get_vendor(self, obj):
        return obj.vendor.name if obj.vendor else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""