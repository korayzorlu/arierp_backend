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


def extract_contract_numbersss(description):
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

def processed_amount(ba_leases):
    total_ba_leases_amount = 0
    for ba_lease in ba_leases:
        total_ba_leases_amount += ba_lease.processed_amount
    return total_ba_leases_amount

def paid_rate(leases):
    paid_rate = 0
    for lease in leases:
        if lease.paid_rate > paid_rate:
            paid_rate = lease.paid_rate
    return paid_rate

def extract_contract_numberss(description):
    # Parantez içindeki tüm numaraları yakalar
    # matches = re.findall(r'sözleşme.*?\(?(\d{4,})[-–]?(\d{0,})\)?', description.lower())
    # contract_numbers = []
    # for match in matches:
    #     contract_numbers.append(match[0])
    #     if match[1]:
    #         contract_numbers.append(match[1])
    # return contract_numbers

    # if not isinstance(description, str):
    #     return []
######
    # pattern = r"""
    #     (?:
    #         sözleşme\s*no[:\s]*       # sözleşme no: 12345
    #         |
    #         sözleşme\s*[:\s]*
    #         |
    #         söz\.?\s*no[:\s]*
    #         |
    #         no[:\s]+
    #         |
    #         nolu\s+sözleşme           # 12345 nolu sözleşme
    #     )
    #     [^\d]*(\d[\d\-_]*)            # sözleşme numarası (rakam, alt çizgi, tire içerebilir)
    # """

    # matches = re.findall(pattern, description.lower(), re.VERBOSE)
    # return matches
######
    if not isinstance(description, str):
        return []

    text = description.lower() # Tüm metni küçük harfe çevir

    matches = []

    # 1. 'sözleşme no', 'no:', 'söz. no', 'nolu sözleşme' gibi tanımlayıcılarla birlikte geçen numaralar
    #    Nokta ile ayrılmış sayıları da yakalamak için [\d\.-_]+ kullanıldı.
    pattern_named = r"""
        (?:
            sözleşme\s*no[:\s]* | # sözleşme no:
            sözleşme\s*[:\s]* | # sözleşme:
            söz\.?\s*no[:\s]* | # söz. no:
            kontrat\s*no[:\s]* | # kontrat no:
            no[:\s]+                  | # no:
            nolu\s+sözleşme             # nolu sözleşme
        )
        [^\d]*([\d\.-_]+)             # numara (rakam, nokta, tire, alt çizgi içerebilir)
    """
    matches.extend(re.findall(pattern_named, text, re.VERBOSE))

    # 2. Parantez içindeki 5+ haneli (veya nokta/tire/alt çizgi içeren) numaralar
    pattern_parens = r'\(([\d\.-_]{5,}(?:[-_]\d{2,})*)\)'
    matches.extend(re.findall(pattern_parens, text))

    # 3. 'sözleşme' kelimesinden hemen önce veya sonra gelen veya içinde geçen numaralar
    # Bu, '48.152 sözleşme' gibi durumları yakalamak için eklendi.
    pattern_proximity = r'(?:\b(\d[\d\.-_]*)\s*sözleşme\b|\bsözleşme\s*(\d[\d\.-_]*)\b)'
    proximity_matches = re.findall(pattern_proximity, text)
    for m in proximity_matches:
        if m[0]: # eğer ilk grup eşleştiyse
            matches.append(m[0])
        if m[1]: # eğer ikinci grup eşleştiyse
            matches.append(m[1])

    # 4. Açıkta geçen 5-12 haneli numaralar (daha dikkatli bir filtreleme ile)
    # Bu kısmı daha güvenli hale getirmek için, banka hareketlerinde TC, IBAN veya tarih gibi sayıları ayırt etmek gerekebilir.
    # Ancak genel bir 'standalone' numara arayışı için kullanılabilir.
    # Şimdilik bu bölümü çok geniş tutmamak adına, sadece belirli bir uzunluktaki sayıları alalım.
    # Daha fazla false positive önlemek için, bu kısmı, eğer diğer kurallar işe yaramazsa son çare olarak kullanmak daha mantıklı olabilir.
    # Örneğin: YIL/AY/GÜN, veya 11 haneli TC, 26 haneli IBAN desenleri dışındaki sayıları hedefleyebiliriz.
    pattern_standalone = r'\b(\d{5,12})\b' # 5-12 haneli sayılar
    raw_standalone_matches = re.findall(pattern_standalone, text)

    # Bulunan tüm eşleşmeleri bir set'e atarak tekrar edenleri kaldır ve temizle
    unique_matches = set()
    for match in matches:
        # Yakalanan numara genellikle string formatında olacaktır.
        # İstenirse burada daha fazla doğrulama veya temizleme yapılabilir (örneğin baştaki/sondaki tireleri kaldırma)
        unique_matches.add(match.strip('-_. ')) # Boşluk, nokta, tire, alt çizgi gibi karakterleri temizle

    # Standalone eşleşmeleri de kontrol edip ekle
    for m in raw_standalone_matches:
        # TC veya IBAN gibi duran sayıları eleyebiliriz, ancak bu her zaman kesin bir çözüm değildir.
        # Bu kısım uygulamanın iş mantığına göre daha fazla geliştirilebilir.
        if m not in unique_matches and len(m) != 11: # Basit bir TC kimlik numarası elemesi
            unique_matches.add(m)

    return list(unique_matches)

def extract_contract_numbersi(description):
    """
    Extract contract numbers from a description string according to the following rules:
    - Contract numbers are usually 4-7 digit numbers.
    - They do not contain punctuation marks in between, except for revised contracts (e.g., 65789/1).
    - Sometimes written with dots (e.g., 48.152), but should be returned without punctuation.
    - There may be more than one contract number in the description.
    - Ignore the last number if it is an 11-digit identity number (TC kimlik).
    - Return only contract numbers as a list of strings. If none found, return an empty list.
    """
    if not isinstance(description, str):
        return []

    text = description.lower()

    # Find all numbers in the text
    all_numbers = re.findall(r'\b\d{4,}\b', text)

    # If last number is 11 digits, ignore it
    if all_numbers and len(all_numbers[-1]) == 11:
        text = text[:text.rfind(all_numbers[-1])]

    # 1. Find numbers with 'sözleşme', 'kontrat', 'no', 'nolu' etc.
    pattern = r"""
        (?:
            sözleşme\s*no[:\s]* | 
            sözleşme\s*[:\s]* | 
            söz\.?\s*no[:\s]* | 
            kontrat\s*no[:\s]* | 
            no[:\s]+ | 
            nolu\s+sözleşme | 
            sözleşme\s*numaralı
        )
        [^\d]*(\d{4,7}(?:/\d{1,2})?)
    """
    matches = re.findall(pattern, text, re.VERBOSE)

    # 2. Find numbers followed or preceded by 'sözleşme' (e.g., '65175 VE 65174 SÖZLEŞME NUMARALI')
    pattern_proximity = r'(\d{4,7}(?:/\d{1,2})?)\s*(?:ve\s*)?sözleşme'
    matches += re.findall(pattern_proximity, text)

    # 3. Find numbers written with dots (e.g., '48.152 sözleşme')
    pattern_dot = r'(\d{1,3}\.\d{3,5})\s*sözleşme'
    dot_matches = re.findall(pattern_dot, text)
    for m in dot_matches:
        matches.append(m.replace('.', ''))

    # 4. Find revised contract numbers (e.g., '65789/1')
    pattern_revised = r'(\d{4,6}/\d{1,2})'
    matches += re.findall(pattern_revised, text)

    # 5. Find standalone 4-7 digit numbers (not TC, not IBAN, not date)
    pattern_standalone = r'\b(\d{4,7})\b'
    raw_standalone = re.findall(pattern_standalone, text)
    for num in raw_standalone:
        if num not in matches and num not in ['2024', '2025', '2023']:
            matches.append(num)

    # Clean up: remove duplicates, strip spaces, filter only 4-7 digit numbers or revised format
    result = set()
    for m in matches:
        m = m.strip()
        if re.fullmatch(r'\d{4,7}', m) or re.fullmatch(r'\d{4,7}/\d{1,2}', m):
            result.add(m)

    return list(result)


def extract_contract_numbers(description):
    matches = []
    
    # normal yazılmış numaralar
    normal_numbers = re.findall(r'\b\d{4,5}\b', description.lower())
    for number in normal_numbers:
        if number not in matches and number not in ['2024', '2025', '2023']:
            matches.append(number)

    #nokta ile ayrılmış numaralar
    dot_numbers = re.findall(r'\b\d{1,2}.\d{3,4}\b', description.lower())
    for number in dot_numbers:
        if number not in matches:
            matches.append(number.replace('.',''))

    #/ ile ayrılmış numaralar
    slash_numbers = re.findall(r'\b\d{4,5}/\d{1,2}\b', description.lower())
    for number in slash_numbers:
        if number not in matches:
            matches.append(number)

    # temizlenmiş ve tekrar edenlerden arındırılmış numaralar
    result = []
    seen = set()
    for match in matches:
        match = match.strip()
        if (re.fullmatch(r'\d{4,5}', match) or re.fullmatch(r'\d{4,5}/\d{1,2}', match)) and match not in seen:
            result.append(match)
            seen.add(match)

    return result
    