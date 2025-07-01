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