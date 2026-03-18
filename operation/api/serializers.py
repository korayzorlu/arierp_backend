from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation

from datetime import date, timedelta
from django.utils import timezone

from contracts.models import *
from companies.models import Company,UserCompany
from operation.models import *
from accounting.models import Invoice
    
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
    process_date = serializers.SerializerMethodField()
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
    
    def get_process_date(self, obj):
        return timezone.now().strftime("%d.%m.%Y")
    
    def get_processed_amount(self, obj):
        ba_leases = obj.partner_advance_activity_partner_advance_activity_leases.all()
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
                    "next_payment" : first_future_payment if first_future_payment else Decimal('0.00'),
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
                "id": obj.lease.uuid,
                "code": obj.lease.code,
                "contract": obj.lease.contract.code if obj.lease.contract else "",
                "lease_status": obj.lease.get_lease_status_display() if hasattr(obj.lease, "get_lease_status_display") else obj.lease.lease_status,
                "partner": obj.lease.contract.partner.name if obj.lease.contract.partner else "",
                "partner_tc": obj.lease.contract.partner.tc_vkn_no if obj.lease.contract else "",
                "partner_crm_code": obj.lease.contract.partner.crm_code if obj.lease.contract else "",
                "project": obj.lease.contract.project if obj.lease.contract else "",
                "block": obj.lease.contract.quotation_obj.quick_quotation.block if obj.lease.contract.quotation_obj.quick_quotation else "",
                "unit": obj.lease.contract.quotation_obj.quick_quotation.unit if obj.lease.contract.quotation_obj.quick_quotation else "",
                "overdue_amount": obj.lease.overdue_amount,
                "processed_amount": obj.lease.processed_amount,
                "overdue_days": obj.lease.overdue_days,
                "currency": obj.lease.currency.code if obj.lease.currency else "",
                "leaseflex_automation": obj.lease.leaseflex_automation,
            }
        else:
            return ""

class TitleDeedInvoiceControlListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    lease_id = serializers.CharField()
    contract = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    contract_uuid = serializers.SerializerMethodField()
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
    item = serializers.SerializerMethodField()
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
    partner_special = serializers.SerializerMethodField()
    quotation = serializers.SerializerMethodField()
    kof = serializers.SerializerMethodField()
    block = serializers.CharField()
    unit = serializers.CharField()
    overdue_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    overdue_days = serializers.IntegerField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    lease_status_update_date = serializers.DateTimeField()
    old_leases = serializers.SerializerMethodField()
    invoices = serializers.SerializerMethodField()
    purchase_documents = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    paid_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    installment_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    transfer_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    #project_list = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ""
    
    def get_contract_uuid(self, obj):
        return obj.contract.uuid if obj.contract else ""

    def get_vendor(self, obj):
        return obj.contract.vendor.name if obj.contract and obj.contract.vendor else ""

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
    
    def get_partner_special(self, obj):
        return True if "special" in obj.contract.partner.types else False
    
    def get_quotation(self, obj):
        return obj.contract.quotation_obj.code if obj.contract.quotation_obj else ""
    
    def get_kof(self, obj):
        return obj.contract.kof if obj.contract else ""
    
    def get_item(self, obj):
        return {
            "id" : obj.item.uuid if obj.item else "",
            "name" : obj.item.stock_name if obj.item else "",
        }

    def get_old_leasess(self, obj):
        old_leases = Lease.objects.select_related().filter(main_lease_id=obj.main_lease_id).order_by('-lease_id')
        
        old_leases_list = []
        for old_lease in old_leases:
            old_leases_list.append({
                "id": old_lease.uuid,
                "code": old_lease.code,
            })
        return old_leases_list
    
    def get_old_leases(self, obj):
        old_leases_map = self.context.get('old_leases_map', {})
        old_leases = old_leases_map.get(obj.main_lease_id, [])
        return [{"id": l.uuid, "code": l.code} for l in old_leases]

    def get_invoicess(self, obj):
        invoices = obj.lease_invoices.all()

        if invoices.exists():
            return "Kesildi"
        else:
            return "Fatura Yok"
        
    def get_invoices(self, obj):
        old_leases_map = self.context.get('old_leases_map', {})
        old_leases = old_leases_map.get(obj.main_lease_id, [])

        invoices_exist = any(lease.lease_invoices.exists() for lease in old_leases)

        if invoices_exist:
            return "Kesildi"
        else:
            return "Fatura Yok"

    def get_purchase_documents(self, obj):
        old_leases_map = self.context.get('old_leases_map', {})
        old_leases = old_leases_map.get(obj.main_lease_id, [])

        purchase_documents_exist = any(lease.lease_purchase_documents.exists() for lease in old_leases)

        if purchase_documents_exist:
            return "Kesildi"
        else:
            return "Fatura Yok"

class UntitleDeedLeaseListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    lease_id = serializers.CharField()
    contract = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    contract_uuid = serializers.SerializerMethodField()
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
    item = serializers.SerializerMethodField()
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
    partner_special = serializers.SerializerMethodField()
    quotation = serializers.SerializerMethodField()
    kof = serializers.SerializerMethodField()
    block = serializers.CharField()
    unit = serializers.CharField()
    overdue_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    overdue_days = serializers.IntegerField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    lease_status_update_date = serializers.DateTimeField()
    old_leases = serializers.SerializerMethodField()
    invoices = serializers.SerializerMethodField()
    purchase_documents = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    paid_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    installment_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    transfer_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    remaining_amount = serializers.SerializerMethodField()
    #project_list = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ""
    
    def get_contract_uuid(self, obj):
        return obj.contract.uuid if obj.contract else ""

    def get_vendor(self, obj):
        return obj.contract.vendor.name if obj.contract and obj.contract.vendor else ""

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
    
    def get_partner_special(self, obj):
        return True if "special" in obj.contract.partner.types else False
    
    def get_quotation(self, obj):
        return obj.contract.quotation_obj.code if obj.contract.quotation_obj else ""
    
    def get_kof(self, obj):
        return obj.contract.kof if obj.contract else ""
    
    def get_item(self, obj):
        return {
            "id" : obj.item.uuid if obj.item else "",
            "name" : obj.item.stock_name if obj.item else "",
        }

    def get_old_leasess(self, obj):
        old_leases = Lease.objects.select_related().filter(main_lease_id=obj.main_lease_id).order_by('-lease_id')
        
        old_leases_list = []
        for old_lease in old_leases:
            old_leases_list.append({
                "id": old_lease.uuid,
                "code": old_lease.code,
            })
        return old_leases_list
    
    def get_old_leases(self, obj):
        old_leases_map = self.context.get('old_leases_map', {})
        old_leases = old_leases_map.get(obj.main_lease_id, [])
        return [{"id": l.uuid, "code": l.code} for l in old_leases]

    def get_invoices(self, obj):
        old_leases_map = self.context.get('old_leases_map', {})
        old_leases = old_leases_map.get(obj.main_lease_id, [])

        invoices_exist = any(lease.lease_invoices.exists() for lease in old_leases)

        if invoices_exist:
            return "Kesildi"
        else:
            return "Fatura Yok"

    def get_purchase_documents(self, obj):
        old_leases_map = self.context.get('old_leases_map', {})
        old_leases = old_leases_map.get(obj.main_lease_id, [])

        purchase_documents_exist = any(lease.lease_purchase_documents.exists() for lease in old_leases)

        if purchase_documents_exist:
            return "Kesildi"
        else:
            return "Fatura Yok"
        
    def get_remaining_amount(self, obj):
        return (obj.installment_amount + obj.transfer_amount) - obj.paid_amount






















