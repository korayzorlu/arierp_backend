from django.http import JsonResponse
from django.utils.timezone import make_aware, localtime
from django.db.models import Q

from decimal import Decimal, InvalidOperation
import re

from leasing.models import *

def is_valid_lease_data(data):
    if not data.get('code') or not data.get('lease'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def is_valid_installment_data(data):
    if not data.get('code') or not data.get('installment'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def get_lease_status_value(display_label):
    LEASE_STATUS_CHOICES = (
        ('aktiflestirildi', ('Aktifleştirildi')),
        ('iptal_edildi', ('İptal Edildi')),
        ('devredildi', ('Devredildi')),
        ('baskasina_transfer_edildi', ('Başkasına Transfer Edildi')),
        ('planlandi', ('Planlandı')),
        ('durduruldu', ('Durduruldu')),
        ('feshedildi', ('Feshedildi')),
        ('revize_edildi', ('Revize Edildi')),
        ('pert', ('Pert')),
        ('envantere_alindi', ('Envantere Alındı')),
        ('para_birimi_degisti', ('Para Birimi Değişti')),
        ('kanuni_takibe_alindi', ('Kanuni Takibe Alındı')),
    )
    
    for value, label in LEASE_STATUS_CHOICES:
        if label == display_label:
            return value
    return None

def format_currency_tr(value):
    try:
        # Sayıya çevirmeye çalış
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        value = Decimal(value).quantize(Decimal("0.01"))

        # Binlik ve ondalık ayracı formatla
        parts = f"{value:,.2f}".split(".")
        integer_part = parts[0].replace(",", ".")
        decimal_part = parts[1]
        return f"{integer_part},{decimal_part}"
    except (InvalidOperation, ValueError, TypeError):
        # Hatalı değer gelirse boş string döndür
        return ""


def extract_contract_numbers(description):
    # Parantez içindeki tüm numaraları yakalar
    matches = re.findall(r'sözleşme.*?\(?(\d{4,})[-–]?(\d{0,})\)?', description.lower())
    contract_numbers = []
    for match in matches:
        contract_numbers.append(match[0])
        if match[1]:
            contract_numbers.append(match[1])
    return contract_numbers

def vendor_filter_for_views(filter_params):
    if filter_params.get('project') == "all":
        return Q()
    elif filter_params.get('project') == "diger":
        return (
            ~Q(partner_contracts__vendor__crm_code__in=["11802","20559","1202","28974","6548","6546"]) &
            ~Q(partner_contracts__project="SAKLI KORU KONAKLARI") &
            ~Q(partner_contracts__project="SİNPAŞ KORU AURA") &
            ~Q(partner_contracts__project="SİNPAŞ TABİAT VİLLALARI") &
            ~Q(partner_contracts__project="METROLİFE PREMİUM") &
            ~Q(partner_contracts__project="METROLİFE") &
            ~Q(partner_contracts__project="METROLIFE PREMİUM") &
            ~Q(partner_contracts__project="METROLIFE") &
            ~Q(partner_contracts__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT") &
            ~Q(partner_contracts__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT-") &
            ~Q(partner_contracts__project="BOULEVARD SEFAKÖY")
        )
    elif filter_params.get('project') == "kizilbuk":
        return Q(partner_contracts__vendor__crm_code__in=["11802","20559"])
    elif filter_params.get('project') == "sinpas":
        return (
            Q(partner_contracts__vendor__crm_code__in=["1202"]) |
            Q(partner_contracts__project="SAKLI KORU KONAKLARI") |
            Q(partner_contracts__project="SİNPAŞ KORU AURA") |
            Q(partner_contracts__project="SİNPAŞ TABİAT VİLLALARI") |
            Q(partner_contracts__project="METROLİFE PREMİUM") |
            Q(partner_contracts__project="METROLİFE") |
            Q(partner_contracts__project="METROLIFE PREMİUM") |
            Q(partner_contracts__project="METROLIFE")
        )
    elif filter_params.get('project') == "kasaba":
        return (
            Q(partner_contracts__vendor__crm_code__in=["28974"]) |
            Q(partner_contracts__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT") |
            Q(partner_contracts__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT-")
        )
    elif filter_params.get('project') == "servet":
        return (
            (
                Q(partner_contracts__vendor__crm_code__in=["6548","6546"]) |
                Q(partner_contracts__project="BOULEVARD SEFAKÖY")
            ) &
            ~Q(partner_contracts__project="SİNPAŞ KORU AURA")
        )
    else:
        return Q(partner_contracts__vendor__crm_code=filter_params.get('project'))

def vendor_filter_for_serializers(filter_params):
    if filter_params.get('project') == "all":
        return Q()
    elif filter_params.get('project') == "diger":
        return (
            ~Q(contract__vendor__crm_code__in=["11802","20559","1202","28974","6548","6546"]) &
            ~Q(contract__project="SAKLI KORU KONAKLARI") &
            ~Q(contract__project="SİNPAŞ KORU AURA") &
            ~Q(contract__project="SİNPAŞ TABİAT VİLLALARI") &
            ~Q(contract__project="METROLİFE PREMİUM") &
            ~Q(contract__project="METROLİFE") &
            ~Q(contract__project="METROLIFE PREMİUM") &
            ~Q(contract__project="METROLIFE") &
            ~Q(contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT") &
            ~Q(contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT-") &
            ~Q(contract__project="BOULEVARD SEFAKÖY")
        )
    elif filter_params.get('project') == "kizilbuk":
        return Q(contract__vendor__crm_code__in=["11802","20559"])
    elif filter_params.get('project') == "sinpas":
        return (
            Q(contract__vendor__crm_code__in=["1202"]) |
            Q(contract__project="SAKLI KORU KONAKLARI") |
            Q(contract__project="SİNPAŞ KORU AURA") |
            Q(contract__project="SİNPAŞ TABİAT VİLLALARI") |
            Q(contract__project="METROLİFE PREMİUM") |
            Q(contract__project="METROLİFE") |
            Q(contract__project="METROLIFE PREMİUM") |
            Q(contract__project="METROLIFE")
        )
    elif filter_params.get('project') == "kasaba":
        return (
            Q(contract__vendor__crm_code__in=["28974"]) |
            Q(contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT") |
            Q(contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT-")
        )
    elif filter_params.get('project') == "servet":
        return (
            (
                Q(contract__vendor__crm_code__in=["6548","6546"]) |
                Q(contract__project="BOULEVARD SEFAKÖY")
            ) &
            ~Q(contract__project="SİNPAŞ KORU AURA")
        )
    else:
        return Q(contract__vendor__crm_code=filter_params.get('project'))

def vendor_filter_for_crm(filter_params):
    if filter_params.get('supplier') == "all":
        return Q()
    elif filter_params.get('supplier') == "diger":
        return (
            ~Q(partner_contracts__vendor__crm_code__in=["11802","20559","1202","28974","6548"])
        )
    elif filter_params.get('supplier') == "kizilbuk":
        return Q(partner_contracts__vendor__crm_code__in=["11802","20559"])
    elif filter_params.get('supplier') == "sinpas":
        return (
            Q(partner_contracts__vendor__crm_code__in=["1202"])
        )
    elif filter_params.get('supplier') == "kasaba":
        return (
            Q(partner_contracts__vendor__crm_code__in=["28974"])
        )
    elif filter_params.get('supplier') == "servet":
        return (
            Q(partner_contracts__vendor__crm_code__in=["6548","6546"])
        )
    else:
        return Q(partner_contracts__vendor__crm_code=filter_params.get('supplier'))

def project_filter_for_views(filter_params):
    if filter_params.get('project') == "all":
        return Q()
    elif filter_params.get('project') == "diger":
        return (
            ~Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT") &
            ~Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            ~Q(partner_contracts__project="BOULEVARD SEFAKÖY") &
            ~Q(partner_contracts__project="BOULEVARD SEFAKÖY-") &
            ~Q(partner_contracts__project="SİNPAŞ KORU AURA") &
            ~Q(partner_contracts__project="SİNPAŞ KORU AURA-") &
            ~Q(partner_contracts__project="METROLIFE") &
            ~Q(partner_contracts__project="METROLIFE-") &
            ~Q(partner_contracts__project="METROLİFE PREMİUM") &
            ~Q(partner_contracts__project="METROLİFE PREMİUM-")
        )
    elif filter_params.get('project') == "kizilbuk":
        return (
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT") |
            Q(partner_contracts__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-")
        )
    elif filter_params.get('project') == "sefakoy":
        return (
            Q(partner_contracts__project="BOULEVARD SEFAKÖY") |
            Q(partner_contracts__project="BOULEVARD SEFAKÖY-")
        )
    elif filter_params.get('project') == "koruaura":
        return (
            Q(partner_contracts__project="SİNPAŞ KORU AURA") |
            Q(partner_contracts__project="SİNPAŞ KORU AURA-")
        )
    elif filter_params.get('project') == "metrolife":
        return (
            Q(partner_contracts__project="METROLIFE") |
            Q(partner_contracts__project="METROLIFE-")
        )
    elif filter_params.get('project') == "metrolifepremium":
        return (
            Q(partner_contracts__project="METROLİFE PREMİUM") |
            Q(partner_contracts__project="METROLİFE PREMİUM-")
        )
    else:
        return Q(contract__project=filter_params.get('project'))

def project_filter_for_serializers(filter_params):
    if filter_params.get('project') == "all":
        return Q()
    elif filter_params.get('project') == "diger":
        return (
            ~Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT") &
            ~Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-") &
            ~Q(contract__project="BOULEVARD SEFAKÖY") &
            ~Q(contract__project="BOULEVARD SEFAKÖY-") &
            ~Q(contract__project="SİNPAŞ KORU AURA") &
            ~Q(contract__project="SİNPAŞ KORU AURA-") &
            ~Q(contract__project="METROLIFE") &
            ~Q(contract__project="METROLIFE-") &
            ~Q(contract__project="METROLİFE PREMİUM") &
            ~Q(contract__project="METROLİFE PREMİUM-")
        )
    elif filter_params.get('project') == "kizilbuk":
        return (
            Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT") |
            Q(contract__project="SİNPAŞ KIZILBÜK THERMAL WELLNESS RESORT-")
        )
    elif filter_params.get('project') == "sefakoy":
        return (
            Q(contract__project="BOULEVARD SEFAKÖY") |
            Q(contract__project="BOULEVARD SEFAKÖY-")
        )
    elif filter_params.get('project') == "koruaura":
        return (
            Q(contract__project="SİNPAŞ KORU AURA") |
            Q(contract__project="SİNPAŞ KORU AURA-")
        )
    elif filter_params.get('project') == "metrolife":
        return (
            Q(contract__project="METROLIFE") |
            Q(contract__project="METROLIFE-")
        )
    elif filter_params.get('project') == "metrolifepremium":
        return (
            Q(contract__project="METROLİFE PREMİUM") |
            Q(contract__project="METROLİFE PREMİUM-")
        )
    else:
        return Q(contract__project=filter_params.get('project'))

def project_text(filter_params):
    if filter_params.get('project') == "diger":
        return "Sinpaş"
    elif filter_params.get('project') == "kizilbuk":
        return "Sinpaş Kızılbük"
    elif filter_params.get('project') == "sinpas":
        return "Sinpaş"
    elif filter_params.get('project') == "kasaba":
        return "Sinpaş Kasaba"
    elif filter_params.get('project') == "servet":
        return "Sinpaş"
    else:
        return "Sinpaş"

def max_overdue_days(leases):
    max_overdue_days = 0
    for lease in leases:
        if lease.overdue_days > max_overdue_days:
            max_overdue_days = lease.overdue_days
    return max_overdue_days

def total_overdue_amount(leases):
    total_overdue_amount = 0
    for lease in leases:
        total_overdue_amount += lease.overdue_amount
    return total_overdue_amount

def total_temerrut_amount(leases):
    total_temerrut_amount = 0
    for lease in leases:
        amount_debits = lease.lease_amount_debits.all()
        for amount_debit in amount_debits:
                total_temerrut_amount += amount_debit.overdue_interest_rate
    return total_temerrut_amount

def paid_rate(leases):
    paid_rate = 0
    for lease in leases:
        if lease.paid_rate > paid_rate:
            paid_rate = lease.paid_rate
    return paid_rate

