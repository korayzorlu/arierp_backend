from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery, F, ExpressionWrapper, DateField,IntegerField,Sum
from django.db.models.functions import Lower,Upper,Cast
from django.utils.timezone import now

from decimal import Decimal
from datetime import date,timedelta,datetime
import logging

from risk.models import *
from risk.utils.filter_utils import to_warned_filters_for_serializers
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from contracts.models import WarningNotice

class AnnualWarnedRiskPartnerListSerializer(serializers.Serializer):
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

        today = now().date()

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            to_warned_filters_for_serializers()
        ).annotate(
            warning_notice_count=Count(
                'contract__contract_warning_notices',
                distinct=True,
                filter=(
                    Q(contract__contract_warning_notices__service_date__isnull=False) &
                    Q(contract__contract_warning_notices__service_date__gte=now()-timedelta(days=365)) &
                    Q(contract__contract_warning_notices__service_date__lte=now())
                )
            ),
        ).filter(warning_notice_count__gt=1)

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                annual_wn_count = lease.contract.contract_warning_notices.filter(
                    service_date__isnull=False,
                    service_date__gte=now()-timedelta(days=365),
                    service_date__lte=now()
                ).count()

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
                    "block" : lease.block or "",
                    "unit" : lease.unit or "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                    "annual_wn_count" : annual_wn_count,
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
        # return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return lease_dict

