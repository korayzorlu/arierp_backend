from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from leasing.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice
from ..filters import *

class TitleDeedConfirm2ListSerializer(serializers.Serializer):
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
                
                if lease.contract.contract_warning_notices.all():
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

class TitleDeedConfirmListSerializer(serializers.Serializer):
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
    
    def get_item(self, obj):
        return {
            "id" : obj.item.uuid if obj.item else "",
            "name" : obj.item.stock_name if obj.item else "",
        }
    
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

