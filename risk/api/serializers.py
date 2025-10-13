from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from risk.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from companies.models import Company,UserCompany
from partners.models import Partner
from contracts.models import WarningNotice
from .filters import AmountDebitTransaction
    
class AmountDebitTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    lease = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    process_group = serializers.CharField()
    due_date = serializers.DateField()
    process_type = serializers.CharField()
    debit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    credit_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    real_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    for_default_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    adat_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    default_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5,decimal_places=2)
    overdue_interest_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    day = serializers.IntegerField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_lease(self, obj):
        return obj.lease.code if obj.lease else ""
    
    def get_partner(self, obj):
        return obj.lease.contract.partner.name if obj.lease.contract.partner and obj.lease.contract and obj.lease else ""
    
    def get_currency(self, obj):
        return obj.lease.currency.code if obj.lease.currency else ""
    
class UnderReviewListSerializer(serializers.Serializer):
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
            Q(is_under_review = True)
        ).order_by("-overdue_days")

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:

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
                    "block" : lease.contract.quotation_obj.quick_quotation.block if lease.contract.quotation_obj.quick_quotation else "",
                    "unit" : lease.contract.quotation_obj.quick_quotation.unit if lease.contract.quotation_obj.quick_quotation else "",
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