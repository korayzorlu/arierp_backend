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
    project = serializers.SerializerMethodField()
    total_contract_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_vendor_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    before_total_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    purchasing = serializers.IntegerField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        if obj.lease:
            return {
                "code" : obj.lease.code,
                "contract" : obj.lease.contract.code if obj.lease.contract else "",
                "partner" : obj.lease.contract.partner.name if obj.lease.contract.partner else "",
                "currency" : obj.lease.currency.code if obj.lease.currency else "",
                "vendor" : obj.lease.contract.vendor.name if obj.lease.contract.vendor else "",
                "project" : obj.lease.contract.project if obj.lease.contract else "",
                "activation_date" : obj.lease.activation_date,
                "contract_date" : "",
                "lease_status" : obj.lease_status,
                "status" : obj.status.name if obj.status else "",
                "vat" : obj.vat,
                "bbsn" : obj.bbsn,
                "is_tufe" : obj.is_tufe
            }
        return obj.lease.code if obj.lease else ''
    
    