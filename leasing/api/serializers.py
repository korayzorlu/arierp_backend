from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from decimal import Decimal
from datetime import date

from leasing.models import *
from companies.models import Company,UserCompany
    
class LeaseListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    contract = serializers.SerializerMethodField()
    type = serializers.CharField()
    vat = serializers.DecimalField(max_digits=5,decimal_places=2)
    activation_date = serializers.DateField()
    lease_status = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    musteri_baz_maliyet = serializers.DecimalField(max_digits=14,decimal_places=2)
    vade = serializers.IntegerField()
    leasing_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    irr = serializers.DecimalField(max_digits=14,decimal_places=2)
    project_no = serializers.CharField()
    project = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    leasing_type = serializers.CharField()
    application_no = serializers.CharField()
    is_last_project = serializers.BooleanField()
    current_request = serializers.CharField()
    finansman_kurum = serializers.CharField()
    is_tufe = serializers.BooleanField()
    is_musterek = serializers.BooleanField()
    bbsn = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    partner_crm_code = serializers.SerializerMethodField()
    quotation = serializers.SerializerMethodField()
    kof = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    overdue_amount = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    def get_lease_status(self, obj):
        return obj.get_lease_status_display() if obj.lease_status else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""
    
    def get_partner(self, obj):
        return obj.contract.partner.name if obj.contract.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.contract.partner.tc_vkn_no if obj.contract.partner else ""
    
    def get_partner_crm_code(self, obj):
        return obj.contract.partner.crm_code if obj.contract.partner else ""
    
    def get_quotation(self, obj):
        return obj.contract.quotation_obj.code if obj.contract.quotation_obj else ""
    
    def get_kof(self, obj):
        return obj.contract.kof if obj.contract else ""
    
    def get_project(self, obj):
        return obj.contract.project if obj.contract else ""
    
    def get_block(self, obj):
        return obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj.quick_quotation else ""
    
    def get_unit(self, obj):
        return obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj.quick_quotation else ""
    
    def get_overdue_amount(self, obj):
        installments = obj.lease_installments.all()
        total_overdue_amount = Decimal("0")
        for installment in installments:
            total_overdue_amount += installment.overdue_amount
        return total_overdue_amount
    
    def get_overdue_days(self, obj):
        installments = obj.lease_installments.all()
        overdue_days = -1
        for installment in installments:
            if installment.overdue_amount > 0:
                today = date.today()
                diff = (today - installment.payment_date).days
                if diff > overdue_days:
                    overdue_days = diff
        return overdue_days

class InstallmentListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    lease_id = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    activation_date = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    payment_date = serializers.DateField()
    vat = serializers.DecimalField(max_digits=5,decimal_places=2)
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    overdue_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    overdue_days = serializers.SerializerMethodField()
    paid = serializers.DecimalField(max_digits=14,decimal_places=2)
    principal = serializers.DecimalField(max_digits=14,decimal_places=2)
    interest = serializers.DecimalField(max_digits=14,decimal_places=2)
    sequency = serializers.IntegerField()
    project = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ""
    
    def get_lease_id(self, obj):
        return obj.lease.uuid if obj.lease else ""
    
    def get_contract(self, obj):
        return obj.lease.contract.code if obj.lease.contract else ""
    
    def get_partner(self, obj):
        return obj.lease.contract.partner.name if obj.lease.contract.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.lease.contract.partner.tc_vkn_no if obj.lease.contract.partner else ""
    
    def get_activation_date(self, obj):
        return obj.lease.activation_date if obj.lease else ""

    def get_currency(self, obj):
        return obj.lease.currency.code if obj.lease.currency else ""
    
    def get_project(self, obj):
        return obj.lease.contract.project if obj.lease.contract else ""
    
    def get_block(self, obj):
        return obj.lease.contract.quotation_obj.quick_quotation.block if obj.lease.contract.quotation_obj.quick_quotation else ""
    
    def get_unit(self, obj):
        return obj.lease.contract.quotation_obj.quick_quotation.unit if obj.lease.contract.quotation_obj.quick_quotation else ""
    
    def get_overdue_days(self, obj):
        today = date.today()
        diff = (today - obj.payment_date).days
        return diff
    
class BankActivityListSerializer(serializers.Serializer):
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
    process_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    currency = serializers.SerializerMethodField()
    receipt_no = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    leases = serializers.SerializerMethodField()

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    def get_leases(self, obj):
        bank_activity_leases = BankActivityLease.objects.filter(bank_activity__uuid = obj.uuid)
        bank_activity_lease_list = []
        if bank_activity_leases:
            for bank_activity_lease in bank_activity_leases:
                installments = bank_activity_lease.lease.lease_installments.all()
                total_overdue_amount = Decimal("0")
                for installment in installments:
                    total_overdue_amount += installment.overdue_amount
                installments = bank_activity_lease.lease.lease_installments.all()

                overdue_days = -1
                for installment in installments:
                    if installment.overdue_amount > 0:
                        today = date.today()
                        diff = (today - installment.payment_date).days
                        if diff > overdue_days:
                            overdue_days = diff

                bank_activity_lease_list.append({
                    "id" : bank_activity_lease.uuid,
                    "code" : bank_activity_lease.lease.code,
                    "contract" : bank_activity_lease.lease.contract.code if bank_activity_lease.lease.contract else "",
                    "lease_status" : bank_activity_lease.lease.lease_status,
                    "partner" : bank_activity_lease.lease.contract.partner.name if bank_activity_lease.lease.contract.partner else "",
                    "partner_tc" : bank_activity_lease.lease.contract.partner.tc_vkn_no if bank_activity_lease.lease.contract else "",
                    "partner_crm_code" : bank_activity_lease.lease.contract.partner.crm_code if bank_activity_lease.lease.contract else "",
                    "project" : bank_activity_lease.lease.contract.project if bank_activity_lease.lease.contract else "",
                    "block" : bank_activity_lease.lease.contract.quotation_obj.quick_quotation.block if bank_activity_lease.lease.contract.quotation_obj.quick_quotation else "",
                    "unit" : bank_activity_lease.lease.contract.quotation_obj.quick_quotation.unit if bank_activity_lease.lease.contract.quotation_obj.quick_quotation else "",
                    "overdue_amount" : total_overdue_amount,
                    "processed_amount" : bank_activity_lease.processed_amount,
                    "overdue_days" : overdue_days,
                    "currency" : bank_activity_lease.lease.currency.code if bank_activity_lease.lease.currency else "",
                    "lease_status" : bank_activity_lease.lease.lease_status,
                    "leaseflex_automation" : bank_activity_lease.leaseflex_automation,
                })
        return sorted(bank_activity_lease_list, key=lambda x: x["overdue_days"], reverse=True)
    
class BankActivityLeaseListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    bank_activity = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)

    def get_bank_activity(self, obj):
        return obj.bank_activity.uuid if obj.bank_activity else ""
    
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
                    "overdue_amount" : obj.total_overdue_amount,
                    "processed_amount" : obj.lease.processed_amount,
                    "overdue_days" : obj.overdue_days,
                    "currency" : obj.lease.currency.code if obj.lease.currency else "",
                    "lease_status" : obj.lease.lease_status,
                    "leaseflex_automation" : obj.lease.leaseflex_automation,
            }
        else:
            return ""