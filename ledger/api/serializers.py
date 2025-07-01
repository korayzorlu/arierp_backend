from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from ledger.models import *
from companies.models import Company,UserCompany
    
class LedgerAccountListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    account_id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    currency = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''