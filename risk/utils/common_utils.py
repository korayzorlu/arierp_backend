from django.conf import settings
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery, F, ExpressionWrapper, DateField,IntegerField,Sum
from django.db.models.functions import Lower,Upper,Cast
from django.utils.timezone import now

from datetime import date,timedelta,datetime

from risk.utils.filter_utils import to_warned_filters_for_views
from leasing.utils.common_utils import vendor_filter_for_views,vendor_filter_for_serializers,project_text,format_currency_tr
from partners.models import *
from leasing.models import Lease, Installment

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
            ~Q(partner_contracts__contract_warning_notices__state__in=['Yeni','Geçerli']) &
            Q(partner_contracts__contract_leases__overdue_days__gt=0) &
            Q(partner_contracts__contract_leases__overdue_days__lte=25) &
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
        today = now().date()

        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            to_warned_filters_for_views()
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
    elif params.get("risk_status") == "to_warned_deposit":
        today = now().date()

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
            Q(partner_contracts__contract_leases__overdue_days__gt=25) &
            (
                Q(partner_contracts__contract_leases__overdue_31_60__gt=0) |
                Q(partner_contracts__contract_leases__overdue_61_90__gt=0) |
                Q(partner_contracts__contract_leases__overdue_91_120__gt=0) |
                Q(partner_contracts__contract_leases__overdue_121_150__gt=0) |
                Q(partner_contracts__contract_leases__overdue_151_180__gt=0) |
                Q(partner_contracts__contract_leases__overdue_181_gte__gt=0)
            ) &
            ~Q(partner_contracts__contract_warning_notices__state__in=['Yeni','Geçerli'])
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
        objs = objs.annotate(
            overdue_days_int=Cast(
                F('partner_contracts__contract_leases__overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'partner_contracts__contract_leases__lease_installments__payment_date',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            first_installment_payment=Max(
                'partner_contracts__contract_leases__lease_installments__payment',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'partner_contracts__contract_contract_payments__credit_amount'
            )
        ).filter(
            (
                Q(first_installment_payment_date=F('expected_payment_date')) &
                Q(first_installment_payment__lte=20000)
            ) |
            Q(total_contract_payments__lte=20000)
        )
    elif params.get("risk_status") == "to_warned_kep":
        today = now().date()

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
            Q(partner_contracts__contract_leases__overdue_days__gt=25) &
            (
                Q(partner_contracts__contract_leases__overdue_31_60__gt=0) |
                Q(partner_contracts__contract_leases__overdue_61_90__gt=0) |
                Q(partner_contracts__contract_leases__overdue_91_120__gt=0) |
                Q(partner_contracts__contract_leases__overdue_121_150__gt=0) |
                Q(partner_contracts__contract_leases__overdue_151_180__gt=0) |
                Q(partner_contracts__contract_leases__overdue_181_gte__gt=0)
            ) &
            ~Q(partner_contracts__contract_warning_notices__state__in=['Yeni','Geçerli'])
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
        objs = objs.annotate(
            overdue_days_int=Cast(
                F('partner_contracts__contract_leases__overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'partner_contracts__contract_leases__lease_installments__payment_date',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            first_installment_payment=Max(
                'partner_contracts__contract_leases__lease_installments__payment',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'partner_contracts__contract_contract_payments__credit_amount'
            )
        ).filter(
            (
                ~Q(first_installment_payment_date=F('expected_payment_date')) &
                Q(first_installment_payment__gt=20000)
            ) |
            Q(total_contract_payments__gt=20000)
        )
    elif params.get("risk_status") == "to_warned_posta":
        today = now().date()

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
            Q(partner_contracts__contract_leases__overdue_days__gt=25) &
            (
                Q(partner_contracts__contract_leases__overdue_31_60__gt=0) |
                Q(partner_contracts__contract_leases__overdue_61_90__gt=0) |
                Q(partner_contracts__contract_leases__overdue_91_120__gt=0) |
                Q(partner_contracts__contract_leases__overdue_121_150__gt=0) |
                Q(partner_contracts__contract_leases__overdue_151_180__gt=0) |
                Q(partner_contracts__contract_leases__overdue_181_gte__gt=0)
            ) &
            ~Q(partner_contracts__contract_warning_notices__state__in=['Yeni','Geçerli'])
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
        objs = objs.annotate(
            overdue_days_int=Cast(
                F('partner_contracts__contract_leases__overdue_days'),
                output_field=IntegerField()
            )
        ).annotate(
            expected_payment_date=ExpressionWrapper(
                today - (F('overdue_days_int') * timedelta(days=1)),
                output_field=DateField()
            ),
            first_installment_payment_date=Max(
                'partner_contracts__contract_leases__lease_installments__payment_date',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            first_installment_payment=Max(
                'partner_contracts__contract_leases__lease_installments__payment',
                filter=Q(partner_contracts__contract_leases__lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'partner_contracts__contract_contract_payments__credit_amount'
            )
        ).filter(
            (
                ~Q(first_installment_payment_date=F('expected_payment_date')) &
                Q(first_installment_payment__gt=20000)
            ) |
            Q(total_contract_payments__gt=20000)
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
            Q(partner_contracts__contract_leases__overdue_days__gt=25) &
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
            Q(partner_contracts__contract_leases__overdue_days__gt=25) &
            Q(partner_contracts__contract_leases__overdue_amount__gt=1000)
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount'),
            warning_notice_count=Count(
                'partner_contracts__contract_warning_notices',
                distinct=True,
                filter=Q(partner_contracts__contract_warning_notices__state__in=['Yeni', 'Geçerli'])
            ),
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
    elif params.get("risk_status") == "today_partners":
        today = date.today()
        
        latest_sequency_subquery = Installment.objects.filter(
            lease=OuterRef('pk')
        ).order_by('-sequency').values('sequency')[:1]

        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_credit=False) &
            Q(partner_contracts__contract_leases__is_last_project=True) &
            Q(partner_contracts__contract_leases__lease_installments__payment_date=today) &
            ~Q(partner_contracts__contract_leases__lease_installments__type='4') &
            ~Q(partner_contracts__contract_leases__lease_installments__sequency=Subquery(latest_sequency_subquery))
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
            Q(types__contains=["special"]) |
            Q(types__contains=["barter"]) |
            Q(types__contains=["virman"])
        )
    elif params.get("risk_status") == "tomorrow_partners":
        tomorrow = date.today() + timedelta(days=1)

        latest_sequency_subquery = Installment.objects.filter(
            lease=OuterRef('pk')
        ).order_by('-sequency').values('sequency')[:1]

        objs = Partner.objects.select_related().filter(
            vendor_filter_for_views(params) &
            (
                Q(partner_contracts__contract_leases__lease_status='aktiflestirildi') |
                Q(partner_contracts__contract_leases__lease_status='planlandi') |
                Q(partner_contracts__contract_leases__lease_status='durduruldu')
            ) &
            Q(partner_contracts__contract_leases__is_credit=False) &
            Q(partner_contracts__contract_leases__is_last_project=True) &
            Q(partner_contracts__contract_leases__lease_installments__payment_date=tomorrow) &
            ~Q(partner_contracts__contract_leases__lease_installments__type='4') &
            ~Q(partner_contracts__contract_leases__lease_installments__sequency=Subquery(latest_sequency_subquery))
        ).annotate(
            max_overdue_days=Max('partner_contracts__contract_leases__overdue_days'),
            total_overdue_amount=Sum('partner_contracts__contract_leases__overdue_amount')
        ).exclude(
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
            Q(overdue_days__lte=25) &
            Q(is_last_project=True) &
            Q(is_kdv_diff=False) &
            Q(is_credit=False) &
            Q(is_under_review=False) &
            ~Q(contract__contract_warning_notices__state__in=['Yeni','Geçerli']) &
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
    elif params.get("risk_status") == "to_warned_deposit":
        today = now().date()

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
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            ~Q(contract__contract_warning_notices__state__in=['Yeni','Geçerli'])
        ).exclude(
             Q(contract__partner__types__contains=["special"]) |
             Q(contract__partner__types__contains=["barter"]) |
             Q(contract__partner__types__contains=["virman"])
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
            first_installment_payment=Max(
                'lease_installments__payment',
                filter=Q(lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'contract__contract_contract_payments__credit_amount'
            )
        ).filter(
            (
                Q(first_installment_payment_date=F('expected_payment_date')) &
                Q(first_installment_payment__lte=20000)
            ) |
            Q(total_contract_payments__lte=20000)
        )
    elif params.get("risk_status") == "to_warned_kep":
        today = now().date()

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
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            ~Q(contract__contract_warning_notices__state__in=['Yeni','Geçerli'])
        ).exclude(
             Q(contract__partner__types__contains=["special"]) |
             Q(contract__partner__types__contains=["barter"]) |
             Q(contract__partner__types__contains=["virman"])
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
            first_installment_payment=Max(
                'lease_installments__payment',
                filter=Q(lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'contract__contract_contract_payments__credit_amount'
            ),
        ).filter(
            (
                ~Q(first_installment_payment_date=F('expected_payment_date')) &
                Q(first_installment_payment__gt=20000)
            ) |
            Q(total_contract_payments__gt=20000)
        )
    elif params.get("risk_status") == "to_warned_posta":
        today = now().date()

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
            Q(overdue_days__gt=25) &
            (
                Q(overdue_31_60__gt=0) |
                Q(overdue_61_90__gt=0) |
                Q(overdue_91_120__gt=0) |
                Q(overdue_121_150__gt=0) |
                Q(overdue_151_180__gt=0) |
                Q(overdue_181_gte__gt=0)
            ) &
            ~Q(contract__contract_warning_notices__state__in=['Yeni','Geçerli'])
        ).exclude(
             Q(contract__partner__types__contains=["special"]) |
             Q(contract__partner__types__contains=["barter"]) |
             Q(contract__partner__types__contains=["virman"])
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
            first_installment_payment=Max(
                'lease_installments__payment',
                filter=Q(lease_installments__sequency=0)
            ),
            total_contract_payments=Sum(
                'contract__contract_contract_payments__credit_amount'
            )
        ).filter(
            (
                ~Q(first_installment_payment_date=F('expected_payment_date')) &
                Q(first_installment_payment__gt=20000)
            ) |
            Q(total_contract_payments__gt=20000)
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
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count(
                'contract__contract_warning_notices',
                distinct=True,
                filter=Q(contract__contract_warning_notices__state__in=['Yeni', 'Geçerli'])
            ),
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
            Q(overdue_days__gt=25) &
            Q(overdue_amount__gt=1000)
        ).annotate(
            warning_notice_count=Count(
                'contract__contract_warning_notices',
                distinct=True,
                filter=Q(contract__contract_warning_notices__state__in=['Yeni', 'Geçerli'])
            ),
        ).filter(warning_notice_count__gt=0).order_by("contract__code","-activation_date").exclude(
            Q(contract__partner__types__contains=["special"]) |
            Q(contract__partner__types__contains=["barter"]) |
            Q(contract__partner__types__contains=["virman"])
        )
    return leases or []

def template_for_risk_status(risk_status):
    if risk_status == "risk_partners":
        return "b84e83786dbcbc132b0b25d293890ba6506ff7d0b474b2aa4e"
    elif risk_status == "to_warned":
        return "c08c6a4b2932d6bdfab0a892b3e74c6109efee6f0d3d9d3c6b"
    elif risk_status == "warned":
        return "a1a4c7f4501d25043d68e5d9bf10f44e8b59b06b1f43a9897a"
    elif risk_status == "to_terminated":
        return ""
    elif risk_status == "today_partners":
        return ""
    elif risk_status == "tomorrow_partners":
        return ""