from django.db.models import Q, Exists, OuterRef

from django.utils.timezone import now

def _active_warning_notice_exists():
    from contracts.models import WarningNotice
    return WarningNotice.objects.filter(
        contract=OuterRef('contract'),
        state__in=['Yeni', 'Geçerli']
    )

def active_warning_notice_exists(self):
    from contracts.models import WarningNotice
    return WarningNotice.objects.filter(
        contract=self.contract,
        state__in=['Yeni', 'Geçerli']
    )

def gecikmede_filters():
    return (
        Q(overdue_amount__gt=100) &
        Q(overdue_days__gt=0) &
        Q(overdue_days__lte=25) &
        ~Exists(_active_warning_notice_exists()) &
        (
            Q(lease_status='aktiflestirildi') |
            Q(lease_status='planlandi') |
            Q(lease_status='durduruldu')
        ) &
        Q(is_last_project=True) &
        Q(is_kdv_diff=False) &
        Q(is_credit=False) &
        Q(is_under_review=False)
    )

def ihtar_cekilecek_filters():
    return (
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
            Q(overdue_0_30__gt=0) |
            Q(overdue_31_60__gt=0) |
            Q(overdue_61_90__gt=0) |
            Q(overdue_91_120__gt=0) |
            Q(overdue_121_150__gt=0) |
            Q(overdue_151_180__gt=0) |
            Q(overdue_181_gte__gt=0)
        ) &
        ~Exists(_active_warning_notice_exists())
    )

def ihtar_cekildi_filters():
    return (
        (
            Q(lease_status='aktiflestirildi') |
            Q(lease_status='planlandi') |
            Q(lease_status='durduruldu')
        ) &
        (
            Q(contract__contract_warning_notices__state='Yeni') |
            Q(contract__contract_warning_notices__state='Geçerli')
        ) &
        Q(is_last_project=True) &
        Q(is_kdv_diff=False) &
        Q(is_credit=False) &
        Q(is_under_review=False) &
        #Q(contract__contract_warning_notices__official_cancellation_date__gt=datetime.today()) &
        Q(overdue_days__gt=25) &
        Q(overdue_amount__gt=1000) &
        ~Q(warning_notice_status='kapsamli_ihtar')
    )

def fesih_edilecek_filters():
    return (
        (
            Q(lease_status='aktiflestirildi') |
            Q(lease_status='planlandi') |
            Q(lease_status='durduruldu')
        ) &
        (
            Q(contract__contract_warning_notices__state='Yeni') |
            Q(contract__contract_warning_notices__state='Geçerli')
        ) &
        Q(is_last_project=True) &
        Q(is_kdv_diff=False) &
        Q(is_credit=False) &
        Q(is_under_review=False) &
        Q(contract__contract_warning_notices__service_date__isnull=False) &
        (
            Q(contract__contract_warning_notices__official_cancellation_date__lte=now().date()) |
            Q(contract__contract_comprehensive_warning_notices__official_cancellation_date__lte=now().date())
        ) &
        Q(overdue_days__gt=25) &
        Q(overdue_amount__gt=1000)
    )

def to_warned_filters_for_views():
    return (
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
            Q(partner_contracts__contract_leases__overdue_0_30__gt=0) |
            Q(partner_contracts__contract_leases__overdue_31_60__gt=0) |
            Q(partner_contracts__contract_leases__overdue_61_90__gt=0) |
            Q(partner_contracts__contract_leases__overdue_91_120__gt=0) |
            Q(partner_contracts__contract_leases__overdue_121_150__gt=0) |
            Q(partner_contracts__contract_leases__overdue_151_180__gt=0) |
            Q(partner_contracts__contract_leases__overdue_181_gte__gt=0)
        ) &
        ~Q(partner_contracts__contract_warning_notices__state__in=['Yeni','Geçerli'])
    )

def to_warned_filters_for_views_lease():
    return (
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
            Q(overdue_0_30__gt=0) |
            Q(overdue_31_60__gt=0) |
            Q(overdue_61_90__gt=0) |
            Q(overdue_91_120__gt=0) |
            Q(overdue_121_150__gt=0) |
            Q(overdue_151_180__gt=0) |
            Q(overdue_181_gte__gt=0)
        ) &
        ~Q(contract__contract_warning_notices__state__in=['Yeni','Geçerli'])
    )

def to_warned_filters_for_serializers():
    return (
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
            Q(overdue_0_30__gt=0) |
            Q(overdue_31_60__gt=0) |
            Q(overdue_61_90__gt=0) |
            Q(overdue_91_120__gt=0) |
            Q(overdue_121_150__gt=0) |
            Q(overdue_151_180__gt=0) |
            Q(overdue_181_gte__gt=0)
        ) &
        ~Q(contract__contract_warning_notices__state__in=['Yeni','Geçerli'])
    )