from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from purchasing.models import *
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice
    
class PurchasePaymentListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    total_contract_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_vendor_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    before_total_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    purchasing = serializers.IntegerField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.lease.contract.code if obj.lease else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ''
    
    def get_partner(self, obj):
        return obj.lease.contract.partner.name if obj.lease else ''
    
    def get_vendor(self, obj):
        return obj.lease.contract.vendor.name if obj.lease else ''
    
    