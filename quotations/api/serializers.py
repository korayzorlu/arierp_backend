from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from quotations.models import *
from companies.models import Company,UserCompany
    
class QuickQuotationListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    customer_type = serializers.CharField()
    project = serializers.CharField()
    block = serializers.CharField()
    unit = serializers.CharField()
    currency = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=14,decimal_places=2)
    vat = serializers.DecimalField(max_digits=5,decimal_places=2)
    customer_signature_date = serializers.DateField()
    unit_delivery_date = serializers.DateField()
    is_tufe = serializers.BooleanField()
    ortalama_tahsil_suresi = serializers.DecimalField(max_digits=5,decimal_places=2)
    devremulk = serializers.CharField()
    start_date = serializers.DateField()
    finish_date = serializers.DateField()
    bbsn = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.partner.tc_vkn_no if obj.partner else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    

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
    
class QuotationListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    quick_quotation = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    kbm = serializers.DecimalField(max_digits=14,decimal_places=2)
    customer_representative = serializers.CharField()
    kof = serializers.CharField()
    request_date = serializers.DateField()
    rev_date = serializers.DateField()
    project = serializers.CharField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.partner.tc_vkn_no if obj.partner else ""
    
    def get_quick_quotation(self, obj):
        return obj.quick_quotation.code if obj.quick_quotation else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    

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