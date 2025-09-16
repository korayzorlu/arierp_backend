from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from datetime import timedelta

from contracts.models import *
from companies.models import Company,UserCompany
    
class ContractInSupplierListSerializer(serializers.Serializer):
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
    
class ContractInProcessListSerializer(serializers.Serializer):
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
    
class ContractInArchiveListSerializer(serializers.Serializer):
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