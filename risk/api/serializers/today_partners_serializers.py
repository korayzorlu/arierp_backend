from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from risk.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from leasing.models import Lease,Installment


class TodayPartnerListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    crm_code = serializers.CharField()
    name = serializers.CharField()
    tc_vkn_no = serializers.SerializerMethodField()
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
    
    def get_leases(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}

        today = date.today()

        # Get the latest sequency for each lease
        latest_sequency_subquery = Installment.objects.filter(
            lease=OuterRef('pk')
        ).values('lease').annotate(
            max_sequency=Max('sequency')
        ).values('max_sequency')

        leases = Lease.objects.select_related("currency","contract","contract__partner","contract__quotation_obj","contract__quotation_obj__quick_quotation").prefetch_related("lease_installments").filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_credit=False) &
            Q(is_last_project=True) &
            Q(lease_installments__payment_date=today) &
            ~Q(lease_installments__sequency=Subquery(latest_sequency_subquery))
        ).order_by("-overdue_days")

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                installments = lease.lease_installments.all()

                today = date.today()
                is_today = False
                for installment in installments:
                    if installment.payment_date == today:
                        is_today = True

                lease_dict["leases"].append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.contract.quotation_obj.quick_quotation.block if lease.contract.quotation_obj.quick_quotation else "",
                    "unit" : lease.contract.quotation_obj.quick_quotation.unit if lease.contract.quotation_obj.quick_quotation else "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_today" : is_today
                })
        #return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return lease_dict

