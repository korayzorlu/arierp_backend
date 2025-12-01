from django.db.models import Q

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
        Q(partner_contracts__contract_warning_notices__isnull=True)
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
        Q(contract__contract_warning_notices__isnull=True)
    )