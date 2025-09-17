from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from datetime import date, timedelta, timezone

from contracts.models import *
from companies.models import Company,UserCompany
from operation.models import *
    
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
    

class PartnerAdvanceActivityListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    bank = serializers.CharField()
    bank_code = serializers.CharField()
    bank_branch_code = serializers.CharField()
    bank_account_no = serializers.CharField()
    cross_bank_code = serializers.CharField()
    cross_bank_branch_code = serializers.CharField()
    cross_bank_account_no = serializers.CharField()
    process_date = serializers.DateTimeField(format = "%d.%m.%Y")
    process_date_date = serializers.DateField(format = "%d.%m.%Y")
    process_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    currency = serializers.SerializerMethodField()
    receipt_no = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    leases = serializers.SerializerMethodField()
    processed_amount = serializers.SerializerMethodField()
    is_processed = serializers.BooleanField()
    is_third_person = serializers.BooleanField()
    is_reliable_person = serializers.BooleanField()
    created_date = serializers.SerializerMethodField()

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    def get_processed_amount(self, obj):
        ba_leases = obj.bank_activity_bank_acitivity_leases.all()
        total_ba_leases_amount = 0
        for ba_lease in ba_leases:
            total_ba_leases_amount += ba_lease.processed_amount
        return total_ba_leases_amount
    
    def get_leases(self, obj):
        partner_advance_activity_leases = PartnerAdvanceActivityLease.objects.select_related().filter(
            Q(partner_advance_activity__uuid = obj.uuid) &
            (
                Q(lease__lease_status='aktiflestirildi') |
                Q(lease__lease_status='planlandi') |
                Q(lease__lease_status='durduruldu')
            )
        )
        partner_advance_activity_lease_list = []
        if partner_advance_activity_leases:
            for partner_advance_activity_lease in partner_advance_activity_leases:
                first_future_payment = (
                    partner_advance_activity_lease.lease.lease_installments
                    .filter(payment_date__gte=timezone.now().date())
                    .order_by('payment_date')
                    .values_list('amount', flat=True)
                    .first()
                )

                partner_advance_activity_lease_list.append({
                    "id" : partner_advance_activity_lease.uuid,
                    "code" : partner_advance_activity_lease.lease.code,
                    "contract" : partner_advance_activity_lease.lease.contract.code if partner_advance_activity_lease.lease.contract else "",
                    "lease_status" : partner_advance_activity_lease.lease.lease_status,
                    "partner" : partner_advance_activity_lease.lease.contract.partner.name if partner_advance_activity_lease.lease.contract.partner else "",
                    "partner_tc" : partner_advance_activity_lease.lease.contract.partner.tc_vkn_no if partner_advance_activity_lease.lease.contract else "",
                    "partner_crm_code" : partner_advance_activity_lease.lease.contract.partner.crm_code if partner_advance_activity_lease.lease.contract else "",
                    "project" : partner_advance_activity_lease.lease.contract.project if partner_advance_activity_lease.lease.contract else "",
                    "block" : partner_advance_activity_lease.lease.contract.quotation_obj.quick_quotation.block if partner_advance_activity_lease.lease.contract.quotation_obj.quick_quotation else "",
                    "unit" : partner_advance_activity_lease.lease.contract.quotation_obj.quick_quotation.unit if partner_advance_activity_lease.lease.contract.quotation_obj.quick_quotation else "",
                    "devremulk" : partner_advance_activity_lease.lease.contract.quotation_obj.quick_quotation.devremulk if partner_advance_activity_lease.lease.contract.quotation_obj.quick_quotation else "",
                    "overdue_amount" : partner_advance_activity_lease.lease.overdue_amount,
                    "processed_amount" : partner_advance_activity_lease.processed_amount,
                    "overdue_days" : partner_advance_activity_lease.lease.overdue_days,
                    "currency" : partner_advance_activity_lease.lease.currency.code if partner_advance_activity_lease.lease.currency else "",
                    "lease_status" : partner_advance_activity_lease.lease.lease_status,
                    "leaseflex_automation" : partner_advance_activity_lease.leaseflex_automation,
                    "next_payment" : first_future_payment,
                    "overdues" : [
                        {   
                            'id': partner_advance_activity_lease.lease.code,
                            'lease': partner_advance_activity_lease.lease.code,
                            'overdue_0_30': partner_advance_activity_lease.lease.overdue_0_30,
                            'overdue_31_60': partner_advance_activity_lease.lease.overdue_31_60,
                            'overdue_61_90': partner_advance_activity_lease.lease.overdue_61_90,
                            'overdue_91_120': partner_advance_activity_lease.lease.overdue_91_120,
                            'overdue_121_150': partner_advance_activity_lease.lease.overdue_121_150,
                            'overdue_151_180': partner_advance_activity_lease.lease.overdue_151_180,
                            'overdue_181_gte': partner_advance_activity_lease.lease.overdue_181_gte,
                        }
                    ]
                })
        return sorted(partner_advance_activity_lease_list, key=lambda x: x["overdue_days"], reverse=True)

    def get_created_date(self, obj):
        return obj.created_date.date()
    
class PartnerAdvanceActivityLeaseListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    partner_advance_activity = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)

    def get_partner_advance_activity(self, obj):
        return obj.partner_advance_activity.uuid if obj.partner_advance_activity else ""
    
    def get_lease(self, obj):
        if obj.lease:
            return {
                    "id" : obj.lease.uuid,
                    "code" : obj.lease.code,
                    "contract" : obj.lease.contract.code if obj.lease.contract else "",
                    "lease_status" : obj.lease.lease_status,
                    "partner" : obj.lease.contract.partner.name if obj.lease.contract.partner else "",
                    "partner_tc" : obj.lease.contract.partner.tc_vkn_no if obj.lease.contract else "",
                    "partner_crm_code" : obj.lease.contract.partner.crm_code if obj.lease.contract else "",
                    "project" : obj.lease.contract.project if obj.lease.contract else "",
                    "block" : obj.lease.contract.quotation_obj.quick_quotation.block if obj.lease.contract.quotation_obj.quick_quotation else "",
                    "unit" : obj.lease.contract.quotation_obj.quick_quotation.unit if obj.lease.contract.quotation_obj.quick_quotation else "",
                    "overdue_amount" : obj.lease.overdue_amount,
                    "processed_amount" : obj.lease.processed_amount,
                    "overdue_days" : obj.lease.overdue_days,
                    "currency" : obj.lease.currency.code if obj.lease.currency else "",
                    "lease_status" : obj.lease.lease_status,
                    "leaseflex_automation" : obj.lease.leaseflex_automation,
            }
        else:
            return ""
