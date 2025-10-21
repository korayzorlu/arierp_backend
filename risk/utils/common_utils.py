from django.conf import settings
from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

from datetime import datetime

from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from partners.models import *
from leasing.models import Lease

def partners_for_project(params):
    if params.get("risk_status") == "risk_partners":
        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_last_project=True) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) &
            Q(partner_contracts__contract_leases__is_credit=False) &
            Q(partner_contracts__contract_leases__is_under_review=False) &
            Q(partner_contracts__contract_warning_notices__isnull=True) &
            Q(partner_contracts__contract_leases__overdue_days__gt=0) &
            Q(partner_contracts__contract_leases__overdue_days__lte=30) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=100)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
    elif params.get("risk_status") == "to_warned":
        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_last_project=True) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) &
            Q(partner_contracts__contract_leases__is_credit=False) &
            Q(partner_contracts__contract_leases__is_under_review=False) &
            Q(partner_contracts__contract_leases__overdue_days__gt=30) &
            (
                Q(partner_contracts__contract_leases__overdue_31_60__gt=0) |
                Q(partner_contracts__contract_leases__overdue_61_90__gt=0) |
                Q(partner_contracts__contract_leases__overdue_91_120__gt=0) |
                Q(partner_contracts__contract_leases__overdue_121_150__gt=0) |
                Q(partner_contracts__contract_leases__overdue_151_180__gt=0) |
                Q(partner_contracts__contract_leases__overdue_181_gte__gt=0)
            ) &
            Q(partner_contracts__contract_warning_notices__isnull=True)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
    elif params.get("risk_status") == "warned":
        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_last_project=True) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) &
            Q(partner_contracts__contract_leases__is_credit=False) &
            Q(partner_contracts__contract_leases__is_under_review=False) &
            Q(partner_contracts__contract_leases__overdue_days__gt=30) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=1000)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    customer_type='individual',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__lte=60, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    customer_type='institutional',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__lte=90, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        ).filter(warning_notice_count__gt=0,overdue_check=True)
    elif params.get("risk_status") == "to_terminated":
        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            (
                Q(partner_contracts__contract_warning_notices__state='Yeni') |
                Q(partner_contracts__contract_warning_notices__state='Geçerli')
            ) &
            Q(partner_contracts__contract_leases__is_last_project=True) &
            Q(partner_contracts__contract_leases__is_kdv_diff=False) &
            Q(partner_contracts__contract_leases__is_credit=False) &
            Q(partner_contracts__contract_leases__is_under_review=False) &
            Q(partner_contracts__contract_warning_notices__official_cancellation_date__lte=datetime.today()) &
            Q(partner_contracts__contract_leases__overdue_days__gt=30) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=1000)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            warning_notice_count=Count('partner_contracts__contract_warning_notices', distinct=True),
            overdue_check=Case(
                When(
                    customer_type='individual',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__gt=60, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                When(
                    customer_type='institutional',
                    then=Case(
                        When(partner_contracts__contract_leases__overdue_days__gt=90, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField()
                    )
                ),
                default=Value(False),
                output_field=BooleanField()
            )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
    return objs or []

def leases_for_project(params):
    partner = Partner.objects.filter(uuid=params.get("partner_id")).first()
    if params.get("risk_status") == "risk_partners":
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = partner) &
            vendor_filter_for_serializers(params) &
            Q(overdue_amount__gt=100) &
            Q(overdue_days__gt=0) &
            Q(overdue_days__lte=30) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__isnull=True) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            )
        ).order_by("-overdue_amount").exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )
    elif params.get("risk_status") == "to_warned":
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = partner) &
            vendor_filter_for_serializers(params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(contract__currency__code="TRY") &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=30) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            Q(contract__contract_warning_notices__isnull=True)
        ).exclude(
             Q(contract__partner__types__contains=["special"]) |
             Q(contract__partner__types__contains=["barter"]) |
             Q(contract__partner__types__contains=["virman"])
        )
    elif params.get("risk_status") == "warned":
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = partner) &
            vendor_filter_for_serializers(params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(contract__currency__code="TRY") &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(overdue_days__gt=30) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True),
            overdue_check=Case(
            When(
                contract__partner__customer_type='individual',
                then=Case(
                    When(overdue_days__lte=60, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            When(
                contract__partner__customer_type='institutional',
                then=Case(
                    When(overdue_days__lte=90, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField()
                )
            ),
            default=Value(False),
            output_field=BooleanField()
        )
        ).filter(warning_notice_count__gt=0,overdue_check=True).exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )
    elif params.get("risk_status") == "to_terminated":
        leases = Lease.objects.select_related().filter(
            Q(contract__partner = partner) &
            vendor_filter_for_serializers(params) &
            (
                Q(lease_status='aktiflestirildi') |
                Q(lease_status='planlandi') |
                Q(lease_status='durduruldu')
            ) &
            Q(contract__currency__code="TRY") &
            (
                Q(contract__contract_warning_notices__state='Yeni') |
                Q(contract__contract_warning_notices__state='Geçerli')
            ) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            Q(contract__contract_warning_notices__official_cancellation_date__lte=datetime.today()) &
            Q(overdue_days__gt=30) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count('contract__contract_warning_notices', distinct=True)
        ).filter(warning_notice_count__gt=0).order_by("contract__code","-activation_date").exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )
    return leases or []
