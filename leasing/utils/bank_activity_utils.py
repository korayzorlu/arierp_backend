from django.db.models import Q
from django.utils import timezone

from decimal import Decimal

def matched_partner_with_tc_vkn_no(params):
    from partners.models import Partner
    obj = Partner.objects.filter(tc_vkn_no=params["tc_vkn_no"]).first()

    return obj

def match_bank_activity_from_iban(params):
    from leasing.models import BankActivity
    objs = BankActivity.objects.select_related().filter(cross_bank_account_no = params["cross_bank_account_no"]).exclude(pk=params["exclude_pk"])
    return objs

def matched_leases_with_contract_numbers(params):
    from leasing.models import Lease
    objs = []
    for contract_number in params["contract_numbers"]:
        obj = Lease.objects.select_related().filter(
            contract__partner=params["partner"],
            is_last_project=True
        ).filter(
            Q(contract__partner=params["partner"]) &
            (
                Q(contract__code=contract_number) |
                Q(contract__code__startswith=f"{contract_number}/")
            ) &
            Q(is_last_project=True)
        ).first()
        if obj:
            objs.append(obj)
    return objs

def matched_leases_with_amount(params):
    from leasing.models import Lease,Installment
    from django.db.models import Sum

    objs = []
    installments = []

    # Lease'leri partner'a göre filtrele
    leases = Lease.objects.select_related().filter(
        Q(contract__partner=params["partner"]) &
        (
            Q(lease_status='aktiflestirildi') |
            Q(lease_status='planlandi') |
            Q(lease_status='durduruldu')
        ) &
        Q(is_last_project=True)
    )

    for lease in leases:
        if lease.overdue_days > 0:
            pass
        next_installment = lease.lease_installments.filter(payment_date__gte=timezone.now().date()).order_by('payment_date').first()
        last_installment = lease.lease_installments.filter().order_by('sequency').last()
        if next_installment and next_installment != last_installment:
            print(f"lease: {lease.code}, amount: {next_installment.amount}")
            installments.append(next_installment)
        elif last_installment:
            print(f"lease: {lease.code}, amount: {last_installment.amount}")
            installments.append(last_installment)
        else:
            print(f"lease: {lease.code}, amount: 0")

    installment_queryset = Installment.objects.filter(
        pk__in=[installment.pk for installment in installments]
    ).order_by('-amount')

    target_amount = params["amount"]
    accumulated = Decimal("0")
    for installment in installment_queryset:
        installment_amount = installment.amount or Decimal("0")
        if accumulated + installment_amount <= target_amount or (installment.lease.overdue_amount > 0 and accumulated + installment.lease.overdue_amount <= target_amount):
            objs.append(installment.lease)
            accumulated += installment_amount
        if accumulated >= target_amount:
            break

    # Eğer tam eşleşme yoksa, en yakın lease'i ekle
    # if not objs and leases.exists():
    #     objs.append(leases.first())

    queryset = Lease.objects.filter(
        pk__in=[obj.pk for obj in objs]
    )

    return queryset

def add_bank_activity_leases(params):
    from leasing.models import Lease,BankActivityLease
    leases = Lease.objects.select_related().filter(
        Q(contract__partner = params["partner"]) &
        (
            Q(lease_status='aktiflestirildi') |
            Q(lease_status='planlandi') |
            Q(lease_status='durduruldu')
        ) &
        Q(is_last_project=True)
    )
    BATCH_SIZE = 1000
    objs = []
    create_objs = []
    for lease in leases:
        obj = BankActivityLease.objects.select_related().filter(
            bank_activity = params["bank_activity"],
            lease = lease
        ).first()
        if obj:
            objs.append(obj)
        else:
            create_objs.append(BankActivityLease(
                company = params["company"],
                bank_activity = params["bank_activity"],
                lease = lease
            ))
            
    if create_objs:
        BankActivityLease.objects.bulk_create(create_objs, batch_size=BATCH_SIZE)

    return objs + create_objs

def match_bank_activity_leases(params):
    from leasing.models import BankActivityLease
    objs = []
    for bank_activity_lease in params["bank_activity_leases"]:
        if bank_activity_lease.lease in params["leases"]:
            objs.append(bank_activity_lease)

    queryset = BankActivityLease.objects.filter(
        pk__in=[obj.pk for obj in objs]
    )
    return queryset

def distribute_amount(params):
    bank_activity_leases = sorted(
        params["bank_activity_leases"],
        key=lambda x: (
            -x.lease.overdue_days,
            -(x.lease.lease_installments.filter(payment_date__gte=timezone.now().date()).order_by('payment_date').values_list('amount', flat=True).first() or 0),
        ),
    )

    remaining_amount = Decimal(str(params["total_amount"]))
    for bank_activity_lease in bank_activity_leases:
        print(f"gecikme gün: {bank_activity_lease.lease.overdue_days}, gecikme tutarı: {bank_activity_lease.lease.overdue_amount}, taksit tutarı: {bank_activity_lease.lease.lease_installments.filter(payment_date__gte=timezone.now().date()).order_by('payment_date').values_list('amount', flat=True).first()}")
        if remaining_amount <= 0:
            break
        
        next_installment = bank_activity_lease.lease.lease_installments.filter(payment_date__gte=timezone.now().date()).order_by('payment_date').first()
        last_installment = bank_activity_lease.lease.lease_installments.filter().order_by('sequency').last()

        if bank_activity_lease.lease.overdue_days > 0:
            bank_activity_lease.processed_amount += min(remaining_amount, bank_activity_lease.lease.overdue_amount)
            bank_activity_lease.leaseflex_automation = True
            bank_activity_lease.save()
            remaining_amount -= bank_activity_lease.processed_amount

        if next_installment and next_installment.amount > 0 and next_installment != last_installment:
            bank_activity_lease.processed_amount += min(remaining_amount, Decimal(str(next_installment.amount)))
            bank_activity_lease.leaseflex_automation = True
            bank_activity_lease.save()
            remaining_amount -= bank_activity_lease.processed_amount
        elif last_installment and last_installment.amount > 0:
            bank_activity_lease.processed_amount += min(remaining_amount, Decimal(str(last_installment.amount)))
            bank_activity_lease.leaseflex_automation = True
            bank_activity_lease.save()
            remaining_amount -= bank_activity_lease.processed_amount

    if bank_activity_leases and remaining_amount > 0:
        bank_activity_leases[0].processed_amount += remaining_amount
        bank_activity_leases[0].leaseflex_automation = True
        bank_activity_leases[0].save()
        remaining_amount = Decimal("0")

    return remaining_amount