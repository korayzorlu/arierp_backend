from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

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
    total_purchase_document_amount = serializers.SerializerMethodField()
    updated_amount = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        if obj.lease:
            return {
                "code" : obj.lease.code,
                "contract" : obj.lease.contract.code if obj.lease.contract else "",
                "partner" : obj.lease.contract.partner.name if obj.lease.contract.partner else "",
                "currency" : obj.lease.currency.code if obj.lease.currency else "",
                "vendor" : obj.lease.contract.supplier if obj.lease.contract else "",
                "project" : obj.lease.contract.project if obj.lease.contract else "",
                "activation_date" : obj.lease.activation_date,
                "contract_date" : "",
                "lease_status" : obj.lease.get_lease_status_display(),
                "status" : obj.lease.status.name if obj.lease.status else "",
                "vat" : obj.lease.vat,
                "bbsn" : obj.lease.bbsn,
                "is_tufe" : obj.lease.is_tufe
            }
        else:
            return ""
    
    def get_diff(self, obj):
        return obj.lease_payment_amount - obj.before_total_payment
    
    def get_temerrut(self, obj):
        return obj.before_total_payment - obj.lease_payment_amount
    
    def get_talimat(self, obj):
        if (obj.lease_payment_amount - obj.before_total_payment) <= 0:
            return obj.vendor_payment_with_report_date
        else:
            return obj.before_total_payment - obj.managing_expense - obj.total_vendor_payment
        
    def get_total_purchase_document_amount(self, obj):
        purchase_documents = PurchaseDocument.objects.select_related().filter(lease = obj.lease).aggregate(total_total_amount=Sum('total_amount'))

        return purchase_documents['total_total_amount'] or Decimal("0.00")
    
    def get_updated_amount(self, obj):
        installments = obj.lease.lease_installments.select_related().filter(
            Q(lease__activation_date__gte=date(2023, 7, 10)) &
            (
                Q(lease__vat=Decimal('18.00')) |
                Q(lease__vat=Decimal('8.00'))
            )
        ).order_by('sequency')

        if installments:
            max_sequency = installments.aggregate(max_seq=Max('sequency'))['max_seq']
            installments = installments.exclude(sequency=max_sequency)
            installments_total = installments.select_related().filter().aggregate(
                total_amount=Sum('amount')
            )
        
            return (installments_total['total_amount']/Decimal('1.18'))*Decimal('1.2') if installments_total['total_amount'] else Decimal('0.00')
        else:
            return Decimal('0.00')
        
class PurchaseDocumentListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    document_id = serializers.CharField()
    code = serializers.CharField()
    document_number = serializers.CharField()
    document_date = serializers.DateField()
    lease = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    currency = serializers.SerializerMethodField()
    exchange_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    document_status = serializers.CharField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        if obj.lease:
            return {
                "code" : obj.lease.code,
                "contract" : obj.lease.contract.code if obj.lease.contract else "",
            }
        else:
            return ""
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_vendor(self, obj):
        return obj.vendor.name if obj.vendor else ""
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    
    