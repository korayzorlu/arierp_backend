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

class ToBeTransferredListSerializer(serializers.Serializer):
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
    partner_note_count = serializers.SerializerMethodField()

    def get_partner_note_count(self, obj):
        return obj.partner_partner_notes.count() if obj.partner_partner_notes.exists() else 0

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

        today = date.today()

        leases = Lease.objects.select_related("contract","contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation","currency").filter(
            Q(contract__partner = obj) &
            project_filter_for_serializers(filter_params) &
            (
                Q(lease_status='planlandi')
            ) &
            Q(is_kdv_diff=False) &
            Q(paid_rate__gte=30) &
            Q(overdue_amount__lte=100) &
            Q(
                lease_installments__type=5,
                lease_installments__payment_date__lt=today
            )
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
                total_lease_temerrut_amount = lease.lease_amount_debits.select_related().aggregate(
                    total=Sum('overdue_interest_rate')
                )['total'] or Decimal("0")

                lease_dict["leases"].append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "contract_id" : lease.contract.contract_id if lease.contract else "",
                    "contract_uuid" : lease.contract.uuid if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.contract.quotation_obj.quick_quotation.block if lease.contract.quotation_obj.quick_quotation else "",
                    "unit" : lease.contract.quotation_obj.quick_quotation.unit if lease.contract.quotation_obj.quick_quotation else "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "temerrut_amount" : total_lease_temerrut_amount,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                })
        return lease_dict

  