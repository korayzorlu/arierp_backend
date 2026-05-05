from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum
from django.utils.timezone import localtime

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from leasing.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice
from .filters import LeaseFilter
    
class LeaseListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
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
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ""
    
    def get_contract_uuid(self, obj):
        return obj.contract.uuid if obj.contract else ""

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
    
    # def get_block(self, obj):
    #     return obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj and obj.contract.quotation_obj.quick_quotation else ""
    
    # def get_unit(self, obj):
    #     return obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj and obj.contract.quotation_obj.quick_quotation else ""
    
    # def get_overdue_days(self, obj):
    #     installments = obj.lease_installments.all()
    #     overdue_days = -1
    #     for installment in installments:
    #         if installment.overdue_amount > 0:
    #             today = date.today()
    #             diff = (today - installment.payment_date).days
    #             if diff > overdue_days:
    #                 overdue_days = diff
    #     return overdue_days

class ActiveLeaseListSerializer(serializers.Serializer):
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
    vendor = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    leasing_type = serializers.CharField()
    application_no = serializers.CharField()
    is_last_project = serializers.BooleanField()
    current_request = serializers.CharField()
    finansman_kurum = serializers.CharField()
    is_tufe = serializers.BooleanField()
    is_musterek = serializers.BooleanField()
    bbsn = serializers.SerializerMethodField()
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
    crm_contract_code = serializers.CharField()
    crm_project_id = serializers.CharField()
    crm_bbsn = serializers.CharField()
    crm_durum = serializers.CharField()
    crm_satici = serializers.CharField()
    crm_invoice_date = serializers.DateField()
    crm_invoice_no = serializers.CharField()
    crm_invoice_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    crm_invoice_kdv_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    crm_invoice_total_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    risk_status = serializers.SerializerMethodField()
    #project_list = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ""
    
    def get_contract_uuid(self, obj):
        return obj.contract.uuid if obj.contract else ""

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
    
    def get_bbsn(self, obj):
        return obj.bbsn if obj.bbsn and obj.bbsn != "None" else ''
    
    def get_item(self, obj):
        return {
            "id" : obj.item.uuid if obj.item else "",
            "name" : obj.item.stock_name if obj.item else "",
        }
    
    def get_vendor(self, obj):
        return {
            "id" : obj.contract.vendor.uuid if obj.contract and obj.contract.vendor else "",
            "name" : obj.contract.vendor.name if obj.contract and obj.contract.vendor else "",
        }
    
    def get_risk_status(self, obj):
        return obj.get_risk_status_display() if obj.risk_status else ""

    
    # def get_block(self, obj):
    #     return obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj and obj.contract.quotation_obj.quick_quotation else ""
    
    # def get_unit(self, obj):
    #     return obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj and obj.contract.quotation_obj.quick_quotation else ""
    
    # def get_project_list(self, obj):
    #     projects = Lease.objects.values_list('item__stock_name', flat=True).distinct()

    #     return projects
    
    # def get_overdue_days(self, obj):
    #     installments = obj.lease_installments.all()
    #     overdue_days = -1
    #     for installment in installments:
    #         if installment.overdue_amount > 0:
    #             today = date.today()
    #             diff = (today - installment.payment_date).days
    #             if diff > overdue_days:
    #                 overdue_days = diff
    #     return overdue_days

class LeaseNoteListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    user = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    title = serializers.CharField()
    text = serializers.CharField()
    date = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.get_full_name() if obj.user else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ''
    
    def get_date(self, obj):
        if obj.created_date:
            return localtime(obj.created_date).strftime("%d.%m.%Y %H:%M")
        return ''


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
    vat_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    payment = serializers.DecimalField(max_digits=14,decimal_places=2)
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    paid = serializers.DecimalField(max_digits=14,decimal_places=2)
    principal = serializers.DecimalField(max_digits=14,decimal_places=2)
    interest = serializers.DecimalField(max_digits=14,decimal_places=2)
    sequency = serializers.IntegerField()
    project = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    type = serializers.CharField()
    type_display = serializers.SerializerMethodField()

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
    
    def get_type_display(self, obj):
        return obj.get_type_display() if obj.type else ""
    

    
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
    process_date_date = serializers.DateField(format = "%d.%m.%Y")
    process_type = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    currency = serializers.SerializerMethodField()
    receipt_no = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    leases = serializers.SerializerMethodField()
    is_processed = serializers.BooleanField()
    is_third_person = serializers.BooleanField()
    is_reliable_person = serializers.BooleanField()
    third_person_status = serializers.CharField()
    created_date = serializers.SerializerMethodField()

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    def get_leases(self, obj):
        bank_activity_leases = BankActivityLease.objects.select_related('lease__contract','lease__currency').prefetch_related('lease__lease_installments').filter(
            Q(bank_activity__uuid = obj.uuid) &
            (
                Q(lease__lease_status='aktiflestirildi') |
                Q(lease__lease_status='planlandi') |
                Q(lease__lease_status='durduruldu')
            )
        ).order_by("-lease__overdue_days")
        bank_activity_lease_list = []
        bank_activity_lease_dict = {"leases": [],"processed_amount": processed_amount(bank_activity_leases) }
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

                first_future_payment = (
                    bank_activity_lease.lease.lease_installments
                    .filter(payment_date__gte=timezone.now().date())
                    .order_by('payment_date')
                    .values_list('amount', flat=True)
                    .first()
                )

                last_payment = (
                    bank_activity_lease.lease.lease_installments
                    .filter()
                    .order_by('sequency')
                    .values_list('amount', flat=True)
                    .last()
                )

                bank_activity_lease_dict["leases"].append({
                    "id" : bank_activity_lease.uuid,
                    "lease_id" : bank_activity_lease.lease.uuid,
                    "code" : bank_activity_lease.lease.code,
                    "contract" : bank_activity_lease.lease.contract.code if bank_activity_lease.lease.contract else "",
                    "lease_status" : bank_activity_lease.lease.lease_status,
                    "partner" : bank_activity_lease.lease.contract.partner.name if bank_activity_lease.lease.contract.partner else "",
                    "partner_tc" : bank_activity_lease.lease.contract.partner.tc_vkn_no if bank_activity_lease.lease.contract else "",
                    "partner_crm_code" : bank_activity_lease.lease.contract.partner.crm_code if bank_activity_lease.lease.contract else "",
                    "project" : bank_activity_lease.lease.contract.project if bank_activity_lease.lease.contract else "",
                    "block" : bank_activity_lease.lease.block if bank_activity_lease.lease and bank_activity_lease else "",
                    "unit" : bank_activity_lease.lease.unit if bank_activity_lease.lease and bank_activity_lease else "",
                    #"devremulk" : bank_activity_lease.lease.contract.quotation_obj.quick_quotation.devremulk if bank_activity_lease.lease.contract.quotation_obj.quick_quotation else "",
                    "devremulk" : bank_activity_lease.lease.period if bank_activity_lease.lease and bank_activity_lease else "",
                    "overdue_amount" : bank_activity_lease.lease.overdue_amount,
                    "processed_amount" : bank_activity_lease.processed_amount,
                    "overdue_days" : bank_activity_lease.lease.overdue_days,
                    "currency" : bank_activity_lease.lease.currency.code if bank_activity_lease.lease.currency else "",
                    "leaseflex_automation" : bank_activity_lease.leaseflex_automation,
                    "next_payment" : first_future_payment,
                    "last_payment" : last_payment,
                    "overdues" : [
                        {   
                            'id': bank_activity_lease.lease.id,
                            'lease': bank_activity_lease.lease.code,
                            'overdue_0_30': bank_activity_lease.lease.overdue_0_30,
                            'overdue_31_60': bank_activity_lease.lease.overdue_31_60,
                            'overdue_61_90': bank_activity_lease.lease.overdue_61_90,
                            'overdue_91_120': bank_activity_lease.lease.overdue_91_120,
                            'overdue_121_150': bank_activity_lease.lease.overdue_121_150,
                            'overdue_151_180': bank_activity_lease.lease.overdue_151_180,
                            'overdue_181_gte': bank_activity_lease.lease.overdue_181_gte,
                        }
                    ]
                })
        #return sorted(bank_activity_lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return bank_activity_lease_dict
    
    def get_created_date(self, obj):
        return obj.created_date.date()
    

    
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
            installments = obj.lease.lease_installments.all()
            total_overdue_amount = Decimal("0")
            for installment in installments:
                total_overdue_amount += installment.overdue_amount

            overdue_days = -1
            for installment in installments:
                if installment.overdue_amount > 0:
                    today = date.today()
                    diff = (today - installment.payment_date).days
                    if diff > overdue_days:
                        overdue_days = diff
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

class ProcessedBankActivityLeaseListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    uuid = serializers.CharField()
    bank_activity = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)

    def get_bank_activity(self, obj):
        return obj.bank_activity.uuid if obj.bank_activity else ""

class RiskPartnerKDVListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    max_overdue_days = serializers.SerializerMethodField()
    total_overdue_amount = serializers.SerializerMethodField()
    leases = serializers.SerializerMethodField()
    special = serializers.SerializerMethodField()
    barter = serializers.SerializerMethodField()
    virman = serializers.SerializerMethodField()
    is_commercial = serializers.BooleanField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
    def get_special(self, obj):
        return True if "special" in obj.types else False
    
    def get_barter(self, obj):
        return True if "barter" in obj.types else False
    
    def get_virman(self, obj):
        return True if "virman" in obj.types else False
    
    def get_max_overdue_days(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=True) &
            Q(is_under_review=False) &
            Q(overdue_amount__gt=100)
        )

        overdue_days = 0
        for lease in leases:
            if lease.overdue_days > overdue_days:
                overdue_days = lease.overdue_days
        return overdue_days
    
    def get_total_overdue_amount(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=True) &
            Q(is_under_review=False) &
            Q(overdue_amount__gt=100)
        )

        overdue_amount = 0
        for lease in leases:
            overdue_amount += lease.overdue_amount
        return overdue_amount
    
    def get_leases(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related("contract","contract__partner","contract__vendor").prefetch_related("contract__contract_warning_notices").filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_kdv_diff=True) &
            Q(is_under_review=False)
        ).order_by("-overdue_days")

        lease_list = []
        if leases:
            for lease in leases:
                installments = lease.lease_installments.all()
                total_overdue_amount = Decimal("0")
                for installment in installments:
                    total_overdue_amount += installment.overdue_amount
                if total_overdue_amount < 100:
                    total_overdue_amount = Decimal("0")
                
                overdue_days = -1
                for installment in installments:
                    if installment.overdue_amount > 0:
                        today = date.today()
                        diff = (today - installment.payment_date).days
                        if diff > overdue_days:
                            overdue_days = diff

                if lease.contract.contract_warning_notices.filter(Q(state__in=['Yeni', 'Geçerli'])).exists():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 30:
                    status = "İhtar Çek"
                else:
                    status = "SMS"

                lease_list.append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.block or "",
                    "unit" : lease.unit or "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                    "statu" : status,
                    "overdues" : [
                        {   
                            'id': lease.code,
                            'lease': lease.code,
                            'overdue_0_30': lease.overdue_0_30,
                            'overdue_31_60': lease.overdue_31_60,
                            'overdue_61_90': lease.overdue_61_90,
                            'overdue_91_120': lease.overdue_91_120,
                            'overdue_121_150': lease.overdue_121_150,
                            'overdue_151_180': lease.overdue_151_180,
                            'overdue_181_gte': lease.overdue_181_gte,
                        }
                    ]
                })
        return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)

class DeliveryConfirmListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    leases = serializers.SerializerMethodField()
    special = serializers.SerializerMethodField()
    barter = serializers.SerializerMethodField()
    virman = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_commercial = serializers.BooleanField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
    def get_special(self, obj):
        return True if "special" in obj.types else False
    
    def get_barter(self, obj):
        return True if "barter" in obj.types else False
    
    def get_virman(self, obj):
        return True if "virman" in obj.types else False
    
    def get_status(self, obj):
        warningNotices = WarningNotice.objects.select_related("contract__partner").filter(contract__partner = obj)
        if warningNotices:
            return "İhtar Çekildi"
        else:
            return ""
    
    def get_leases(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related("contract","contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation","currency").filter(
            Q(contract__partner = obj) &
            project_filter_for_serializers(filter_params) &
            (
                Q(lease_status='planlandi')
            ) &
            Q(is_kdv_diff=False) &
            Q(paid_rate__gte=30) &
            Q(overdue_amount__lte=100)
        )

        excluded_leases = Lease.objects.select_related("contract__partner").filter(
            Q(contract__partner = obj) &
            project_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        ).exclude(
            id__in=leases.values_list('id', flat=True)
        ).aggregate(total_overdue_amount=Sum('overdue_amount'))
        

        # excluded_leases = Lease.objects.select_related().filter(
        #     Q(contract__partner = obj) &
        #     project_filter_for_serializers(filter_params) &
        #     (
        #         Q(lease_status='planlandi')
        #     ) &
        #     Q(is_kdv_diff=False) &
        #     Q(overdue_amount__gt=100)
        # ).aggregate(total_overdue_amount=Sum('overdue_amount'))

        lease_dict = {
            "leases": [],
            "total_overdue_amount": total_overdue_amount(leases),
            "total_excluded_overdue_amount": excluded_leases['total_overdue_amount'] if excluded_leases['total_overdue_amount'] else Decimal("0"),
            "max_overdue_days": max_overdue_days(leases),
            "total_temerrut_amount": total_temerrut_amount(leases),
            "paid_rate": paid_rate(leases)
        }
        if leases:
            for lease in leases:
                # amount_debits = lease.lease_amount_debits.all()

                # total_lease_temerrut_amount = Decimal("0")
                # for amount_debit in amount_debits:
                #     total_lease_temerrut_amount += amount_debit.overdue_interest_rate

                total_lease_temerrut_amount = lease.lease_amount_debits.select_related().aggregate(
                    total=Sum('overdue_interest_rate')
                )['total'] or Decimal("0")
                
                if lease.contract.contract_warning_notices.filter(Q(state__in=['Yeni', 'Geçerli'])).exists():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 30:
                    status = "İhtar Çek"
                else:
                    status = "SMS"

                lease_dict["leases"].append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.block or "",
                    "unit" : lease.unit or "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "temerrut_amount" : total_lease_temerrut_amount,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                    "status" : status
                })
        return lease_dict

   
class DepositPartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    max_overdue_days = serializers.SerializerMethodField()
    total_overdue_amount = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    leases = serializers.SerializerMethodField()
    special = serializers.SerializerMethodField()
    barter = serializers.SerializerMethodField()
    virman = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_commercial = serializers.BooleanField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
    def get_special(self, obj):
        return True if "special" in obj.types else False
    
    def get_barter(self, obj):
        return True if "barter" in obj.types else False
    
    def get_virman(self, obj):
        return True if "virman" in obj.types else False
    
    def get_status(self, obj):
        warningNotices = WarningNotice.objects.select_related("contract__partner").filter(contract__partner = obj)
        if warningNotices:
            return "İhtar Çekildi"
        else:
            return ""
    
    def get_max_overdue_days(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            Q(contract__partner = obj) &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        )

        overdue_days = 0
        for lease in leases:
            if lease.overdue_days > overdue_days:
                overdue_days = lease.overdue_days
        return overdue_days
    
    def get_total_overdue_amount(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            Q(contract__partner = obj) &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=30) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        )

        overdue_amount = 0
        for lease in leases:
            overdue_amount += lease.overdue_amount
        return overdue_amount
    
    def get_total_paid(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            Q(contract__partner = obj) &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        )

        paid = 0
        for lease in leases:
            paid += lease.paid
        return paid
    
    def get_leases(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}
        
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            Q(contract__partner = obj) &
            Q(paid__lte=10000) &
            Q(paid__gte=1000) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        ).order_by("-overdue_days")

        # if str(filter_params.get('project')) == "diger":
        #     leases = leases.exclude(contract__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
        # elif str(filter_params.get('project')) == "kizilbuk":
        #     leases = leases.filter(contract__vendor__crm_code__in=["11802","20559"])
        # else:
        #     leases = leases.filter(contract__vendor__crm_code=str(filter_params.get('project')))

        lease_list = []
        if leases:
            for lease in leases:

                if lease.contract.contract_warning_notices.filter(Q(state__in=['Yeni', 'Geçerli'])).exists():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 30:
                    status = "İhtar Çek"
                else:
                    status = "SMS"

                lease_list.append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.block or "",
                    "unit" : lease.unit or "",
                    "overdue_amount" : lease.overdue_amount,
                    "paid" : lease.paid,
                    "overdue_days" : lease.overdue_days,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                    "status" : status,
                    "overdues" : [
                        {   
                            'id': lease.code,
                            'lease': lease.code,
                            'overdue_0_30': lease.overdue_0_30,
                            'overdue_31_60': lease.overdue_31_60,
                            'overdue_61_90': lease.overdue_61_90,
                            'overdue_91_120': lease.overdue_91_120,
                            'overdue_121_150': lease.overdue_121_150,
                            'overdue_151_180': lease.overdue_151_180,
                            'overdue_181_gte': lease.overdue_181_gte,
                        }
                    ]
                })
        return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)

class AgreedTerminatedPartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
    leases = serializers.SerializerMethodField()
    special = serializers.SerializerMethodField()
    barter = serializers.SerializerMethodField()
    virman = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_commercial = serializers.BooleanField()

    def get_tc_vkn_no(self, obj):
        return obj.vat_no if obj.customer_type == "institutional" else obj.tc_vkn_no
    
    def get_special(self, obj):
        return True if "special" in obj.types else False
    
    def get_barter(self, obj):
        return True if "barter" in obj.types else False
    
    def get_virman(self, obj):
        return True if "virman" in obj.types else False
    
    def get_status(self, obj):
        warningNotices = WarningNotice.objects.select_related("contract__partner").filter(contract__partner = obj)
        if warningNotices:
            return "İhtar Çekildi"
        else:
            return ""
    
    def get_leases(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}
        
        leases = Lease.objects.select_related("contract","contract__partner","contract__vendor").prefetch_related("contract__contract_warning_notices").filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            Q(contract__partner = obj) &
            Q(is_agreed_terminated=True)
        ).order_by("-overdue_days")

        # if str(filter_params.get('project')) == "diger":
        #     leases = leases.exclude(contract__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
        # elif str(filter_params.get('project')) == "kizilbuk":
        #     leases = leases.filter(contract__vendor__crm_code__in=["11802","20559"])
        # else:
        #     leases = leases.filter(contract__vendor__crm_code=str(filter_params.get('project')))

        max_overdue_days = 0
        for lease in leases:
            if lease.overdue_days > max_overdue_days:
                max_overdue_days = lease.overdue_days

        total_overdue_amount = 0
        for lease in leases:
            total_overdue_amount += lease.overdue_amount

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount, "max_overdue_days": max_overdue_days }
        if leases:
            for lease in leases:

                if lease.contract.contract_warning_notices.filter(Q(state__in=['Yeni', 'Geçerli'])).exists():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 30:
                    status = "İhtar Çek"
                else:
                    status = "SMS"

                lease_dict["leases"].append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.block or "",
                    "unit" : lease.unit or "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                    "status" : status,
                    "overdues" : [
                        {   
                            'id': lease.code,
                            'lease': lease.code,
                            'overdue_0_30': lease.overdue_0_30,
                            'overdue_31_60': lease.overdue_31_60,
                            'overdue_61_90': lease.overdue_61_90,
                            'overdue_91_120': lease.overdue_91_120,
                            'overdue_121_150': lease.overdue_121_150,
                            'overdue_151_180': lease.overdue_151_180,
                            'overdue_181_gte': lease.overdue_181_gte,
                        }
                    ]
                })
        #return sorted(lease_dict, key=lambda x: x["leases"]["overdue_days"], reverse=True)
        return lease_dict