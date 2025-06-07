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