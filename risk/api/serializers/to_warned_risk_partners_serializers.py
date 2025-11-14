from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery, F, ExpressionWrapper, DateField,IntegerField
from django.db.models.functions import Lower,Upper,Cast
from django.utils.timezone import now

from decimal import Decimal
from datetime import date,timedelta,datetime
import logging

from risk.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from contracts.models import WarningNotice

class ToWarnedRiskPartnerListSerializer(serializers.Serializer):
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

        today = now().date()

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        )

        leases = leases.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).filter(
            first_installment_payment_date=F('expected_payment_date')
        )

        latest_lease = leases.filter(
            contract__code=OuterRef('contract__code')
        ).order_by('-activation_date')

        leases = leases.filter(
            id=Subquery(latest_lease.values('id')[:1])
        )

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                if lease.contract.contract_warning_notices.all():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 25:
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
        # return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return lease_dict

class DepositeToWarnedRiskPartnerListSerializer(serializers.Serializer):
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

        today = now().date()

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        )

        leases = leases.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            ),
            first_installment_amount=F(
                'lease_installments__amount',
                filter=Q(lease_installments__sequency=0)
            )
        ).filter(
            first_installment_payment_date=F('expected_payment_date'),
            first_installment_amount__lte=20000
        )

        # latest_lease = leases.filter(
        #     contract__code=OuterRef('contract__code')
        # ).order_by('-activation_date')

        # leases = leases.filter(
        #     id=Subquery(latest_lease.values('id')[:1])
        # )

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                if lease.contract.contract_warning_notices.all():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 25:
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
        # return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return lease_dict

class KepToWarnedRiskPartnerListSerializer(serializers.Serializer):
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

        today = now().date()

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            #Q(lease_trade_transactions__amount_type=0) &
            Q(contract__partner__is_turkkep=True)
        )

        leases = leases.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        )

        # latest_lease = leases.filter(
        #     contract__code=OuterRef('contract__code')
        # ).order_by('-activation_date')

        # leases = leases.filter(
        #     id=Subquery(latest_lease.values('id')[:1])
        # )

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                if lease.contract.contract_warning_notices.all():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 25:
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
        # return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return lease_dict

class PostaToWarnedRiskPartnerListSerializer(serializers.Serializer):
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

        today = now().date()

        leases = Lease.objects.select_related().filter(
            Q(contract__partner = obj) &
            vendor_filter_for_serializers(filter_params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True) &
            #Q(lease_trade_transactions__amount_type=0) &
            Q(contract__partner__is_turkkep=False)
        )

        leases = leases.annotate(
            overdue_days_int=Cast(
                F('overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'lease_installments__payment_date',
                filter=Q(lease_installments__sequency=0)
            )
        ).exclude(
            first_installment_payment_date=F('expected_payment_date')
        )


        # latest_lease = leases.filter(
        #     contract__code=OuterRef('contract__code')
        # ).order_by('-activation_date')

        # leases = leases.filter(
        #     id=Subquery(latest_lease.values('id')[:1])
        # )

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                if lease.contract.contract_warning_notices.all():
                    status = "İhtar Çekildi"
                elif lease.is_kdv_diff:
                    status = "KDV Farkı"
                elif lease.overdue_amount > 1000 and lease.overdue_days > 25:
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
        # return sorted(lease_list, key=lambda x: x["overdue_days"], reverse=True)
        return lease_dict
