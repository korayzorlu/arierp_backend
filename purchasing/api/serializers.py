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
    lease = serializers.SerializerMethodField()
    total_contract_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_vendor_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    before_total_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    after_total_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    managing_expense = serializers.DecimalField(max_digits=14,decimal_places=2)
    lease_payment_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    vendor_payment_with_report_date = serializers.DecimalField(max_digits=14,decimal_places=2)
    next_payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    purchasing = serializers.IntegerField()
    diff = serializers.SerializerMethodField()
    temerrut = serializers.SerializerMethodField()
    talimat = serializers.SerializerMethodField()

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
                "lease_status" : obj.lease.get_lease_status_display(),
                "status" : obj.lease.status.name if obj.lease.status else "",
                "vat" : obj.lease.vat,
                "bbsn" : obj.lease.bbsn,
                "is_tufe" : obj.lease.is_tufe
            }
        return obj.lease.code if obj.lease else ''
    
    def get_diff(self, obj):
        return obj.lease_payment_amount - obj.before_total_payment
    
    def get_temerrut(self, obj):
        return obj.lease_payment_amount - obj.before_total_payment
    
    def get_talimat(self, obj):
        if (obj.lease_payment_amount - obj.before_total_payment) <= 0:
            return obj.vendor_payment_with_report_date
        else:
            return obj.before_total_payment - obj.managing_expense - obj.total_vendor_payment
    
    