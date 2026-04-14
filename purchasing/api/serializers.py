from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum,F

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
                "bbsn" : obj.lease.bbsn if obj.lease.bbsn is not None or obj.lease.bbsn == "None" else "",
                "ifs_tahsilat" : obj.lease.ifs_tahsilat,
                "is_tufe" : obj.lease.is_tufe,
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
        # if obj.lease.activation_date and obj.lease.activation_date >= date(2023, 7, 10) and (obj.lease.vat == Decimal('18.00') or obj.lease.vat == Decimal('8.00')):
        max_sequency_for_installment = obj.lease.lease_installments.aggregate(max_seq=Max('sequency'))['max_seq']
        if (obj.lease.vat == Decimal('18.00') or obj.lease.vat == Decimal('8.00')) and obj.lease.lease_installments.filter(payment_date__gte=date(2023, 7, 10)).exclude(sequency=max_sequency_for_installment).exists() and obj.lease.is_last_project:
            next_installments_total_total = Decimal('0.00')
            next_installments = obj.lease.lease_installments.select_related().filter(
                Q(payment_date__gte=date(2023, 7, 10)) &
                (
                    Q(lease__vat=Decimal('18.00')) |
                    Q(lease__vat=Decimal('8.00'))
                )
            ).order_by('sequency')

            kdv_rate = Decimal('1.18') if obj.lease.vat == Decimal('18.00') else Decimal('1.08')
            kdv_new_rate = Decimal('1.2') if obj.lease.vat == Decimal('18.00') else Decimal('1.1')

            if next_installments:
                max_sequency = next_installments.aggregate(max_seq=Max('sequency'))['max_seq']
                next_installments = next_installments.exclude(sequency=max_sequency)
                next_installments_total = next_installments.select_related().filter().aggregate(
                    total_amount=Sum('amount')
                )

                next_installments_total_total = (next_installments_total['total_amount'] / kdv_rate) * kdv_new_rate if next_installments_total['total_amount'] else Decimal('0.00')

            prev_installments_total_total = Decimal('0.00')
            prev_installments = obj.lease.lease_installments.select_related().filter(
                Q(payment_date__lt=date(2023, 7, 10)) &
                (
                    Q(lease__vat=Decimal('18.00')) |
                    Q(lease__vat=Decimal('8.00'))
                )
            ).order_by('sequency')

            if prev_installments:
                max_sequency = prev_installments.aggregate(max_seq=Max('sequency'))['max_seq']
                prev_installments = prev_installments.exclude(sequency=max_sequency)
                prev_installments_total = prev_installments.select_related().filter().aggregate(
                    total_amount=Sum('amount')
                )

                prev_installments_total_total = prev_installments_total['total_amount'] if prev_installments_total['total_amount'] else Decimal('0.00')

                return prev_installments_total_total + next_installments_total_total
            else:
                return obj.total_contract_amount if obj.total_contract_amount else Decimal('0.00')
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
    purchase_document_items = serializers.SerializerMethodField()
    crm_amount = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        if obj.lease:
            return {
                "code" : obj.lease.code,
                "contract" : obj.lease.contract.code if obj.lease.contract else "",
                "bbsn" : obj.lease.bbsn if obj.lease.bbsn is not None or obj.lease.bbsn == "None" else "",
            }
        else:
            return ""
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_vendor(self, obj):
        return obj.vendor.name if obj.vendor else ""
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    def get_purchase_document_items(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}
        
        purchase_document_items = PurchaseDocumentItem.objects.select_related().prefetch_related().filter(
            Q(purchase_document = obj)
        ).order_by("id")

        purchase_document_item_dict = {"purchase_document_items": []}
        if purchase_document_items:
            for purchase_document_item in purchase_document_items:
                purchase_document_item_dict["purchase_document_items"].append({
                    "id" : purchase_document_item.uuid,
                    "document_line_id" : purchase_document_item.document_line_id,
                    "purchase_document" : obj.document_number,
                    "stock_name" : purchase_document_item.stock_name,
                    "description" : purchase_document_item.description,
                    "unit_amount" : purchase_document_item.unit_amount,
                    "amount" : purchase_document_item.amount,
                    "vat_amount" : purchase_document_item.vat_amount,
                    "total_amount" : purchase_document_item.total_amount,
                    "quantity" : purchase_document_item.quantity,
                })
        return purchase_document_item_dict
    
    def get_crm_amount(self, obj):
        return obj.lease.crm_invoice_total_amount if obj.lease else Decimal('0.00')
    
    
class PurchaseDocumentItemListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    document_line_id = serializers.CharField()
    purchase_document = serializers.SerializerMethodField()
    stock_name = serializers.CharField()
    description = serializers.CharField()
    unit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    vat_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    quantity = serializers.IntegerField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_purchase_document(self, obj):
        return obj.purchase_document.code if obj.purchase_document else ""