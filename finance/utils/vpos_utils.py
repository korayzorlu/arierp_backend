from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.http import JsonResponse
from django.utils.timezone import now,localtime

import requests
from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
import re
import os
import random
import string
import logging
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from lxml import etree
import unicodedata
from difflib import SequenceMatcher
from enum import Enum


from finance.models import *
from common.models import Currency, ExchangeRate
from common.utils.common_utils import parse_datetime,safe_decimal
from underwriting.utils import check_third_person_status_vpos
from compliance.utils.third_person_utils import create_third_person_vpos

class NameMatch(str, Enum):
    MATCH = "match"          # Normalize edilince aynı isim
    REVIEW = "review"        # Benziyor ama aynı kişi olduğu kesin değil
    NO_MATCH = "no_match"    # Farklı isim

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
FUZZY_THRESHOLD = 0.85

def normalize_name(value) -> str:
    text = str(value or "").translate(TR_MAP)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z]+", " ", text.casefold())
    return text.strip()

def compare_names(isim, soyisim, kart_sahibi) -> NameMatch:
    first = normalize_name(isim)
    last = normalize_name(soyisim)
    card = normalize_name(kart_sahibi)

    if not first or not last or not card:
        return NameMatch.NO_MATCH

    compact_card = card.replace(" ", "")
    candidates = (
        f"{first}{last}".replace(" ", ""),
        f"{last}{first}".replace(" ", ""),
    )

    # Büyük/küçük harf, Türkçe karakter, boşluk ve ad-soyad sırası farkları
    if compact_card in candidates:
        return NameMatch.MATCH

    # Eksik ikinci isim veya ad sırası farkı: Mehmet Ali Yılmaz / Mehmet Yılmaz
    expected_tokens = set(f"{first} {last}".split())
    card_tokens = set(card.split())
    shorter, longer = sorted((expected_tokens, card_tokens), key=len)
    if len(shorter) >= 2 and shorter <= longer:
        return NameMatch.REVIEW

    # Yazım hatası: Mehmet / Mehmat
    best_ratio = max(
        SequenceMatcher(None, candidate, compact_card).ratio()
        for candidate in candidates
    )
    if best_ratio >= FUZZY_THRESHOLD:
        return NameMatch.REVIEW

    return NameMatch.NO_MATCH

def is_valid_vpos_transaction_data(data):
    parameters = [
        'CompanyId', 'ValidationKey', 'ProcessDate', 'MusteriTipi', 'PaidAmount',
        'LeasePostingGroupId', 'FirmaAdi', 'KurumTipi', 'VergiDairesi', 'VergiNo',
        'WebSitesi', 'Adres', 'Ulke', 'Sehir', 'Ilce', 'Posta', 'IletisimList',
        'Ad', 'IkinciAd', 'OrtaAd', 'SoyAd', 'Cinsiyet', 'TCKimlikNo', 'PasaportNo',
        'Uyruk', 'DogumTarih', 'VergiDairesi_Birey', 'VergiNo_Birey', 'Adres_Birey',
        'Ulke_Birey', 'Sehir_Birey', 'Ilce_Birey', 'Posta_Birey', 'IletisimList_Birey',
        'UserName', 'Password', 'Telefon', 'EMail', 'Fax', 'BankCode', 'ContractCode',
        'CurrencyCode', 'ExtTransactionId','KartAdSoyad'
    ]

    unknown_keys = set(data.keys()) - set(parameters)
    if unknown_keys:
        return False, JsonResponse({'message': f'Geçersiz parametre(ler): {", ".join(sorted(unknown_keys))}', 'status': 'error'}, status=400)

    if not data.get('CompanyId') or not Company.objects.filter(uuid=data.get('CompanyId')).exists():
        return False, JsonResponse({'message': 'Şirket bilgisi eksik veya geçersiz! (CompanyId)','status':'error'}, status=400)
    
    if not data.get('ValidationKey') or data.get('ValidationKey') != settings.VPOS_VALIDATION_KEY:
        return False, JsonResponse({'message': 'Doğrulama anahtarı geçersiz! (ValidationKey)','status':'error'}, status=400)

    if data.get('ExtTransactionId') == "35700686420507101692" or data.get('ExtTransactionId') == "20170728426114674433":
        return False, JsonResponse({'message': 'Başarıyla kaydedildi!','status':'success'}, status=200)
    if not data.get('ExtTransactionId') or VPosTransaction.objects.filter(ext_transaction_id=data.get('ExtTransactionId'),lease_posting_group_id=data.get('LeasePostingGroupId')).exists():
        return False, JsonResponse({'message': 'ExtTransactionId eksik veya zaten gönderilmiş! (ExtTransactionId)','status':'error'}, status=400)
    
    # if not data.get('UserName') or not data.get('Password'):
    #     return False, JsonResponse({'message': 'Kullanıcı adı veya şifre eksik! (UserName, Password)','status':'error'}, status=400)
    
    if not data.get('ProcessDate') or not parse_datetime(data.get('ProcessDate')):
        return False, JsonResponse({'message': 'İşlem tarihi eksik veya geçersiz! (ProcessDate)','status':'error'}, status=400)

    if not data.get('MusteriTipi') or not isinstance(data.get('MusteriTipi'), int) or data.get('MusteriTipi') not in [1, 2]:
        return False, JsonResponse({'message': 'Müşteri tipi eksik veya geçersiz! (MusteriTipi)','status':'error'}, status=400)
    
    if not data.get('PaidAmount') or not isinstance(data.get('PaidAmount'), (int, float, Decimal)) or Decimal(data.get('PaidAmount')) <= 0:
        return False, JsonResponse({'message': 'Ödenen tutar eksik veya geçersiz! (PaidAmount)','status':'error'}, status=400)
    
    if not data.get('CurrencyCode') or not Currency.objects.filter(code='TRY' if data.get('CurrencyCode') == 'TL' else data.get('CurrencyCode')).exists():
        return False, JsonResponse({'message': 'Para birimi eksik veya geçersiz! (CurrencyCode)','status':'error'}, status=400)
    
    if not isinstance(data.get('LeasePostingGroupId'), bool):
        return False, JsonResponse({'message': 'İşlem grubu eksik veya geçersiz! (LeasePostingGroupId)','status':'error'}, status=400)

    if not data.get('DogumTarih'):
        return False, JsonResponse({'message': 'Doğum tarihi eksik! (DogumTarih)','status':'error'}, status=400)

    str_fields = [
        'FirmaAdi', 'KurumTipi', 'VergiDairesi', 'VergiNo', 'WebSitesi',
        'Adres', 'Ulke', 'Sehir', 'Ilce', 'Posta',
        'Ad', 'IkinciAd', 'OrtaAd', 'SoyAd', 'Cinsiyet',
        'TCKimlikNo', 'PasaportNo', 'Uyruk', 'DogumTarih',
        'VergiDairesi_Birey', 'VergiNo_Birey', 'Adres_Birey',
        'Ulke_Birey', 'Sehir_Birey', 'Ilce_Birey', 'Posta_Birey',
        'UserName', 'Password', 'Telefon', 'EMail', 'Fax',
        'BankCode', 'ContractCode', 'ExtTransactionId','KartAdSoyad'
    ]
    for field in str_fields:
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            return False, JsonResponse({'message': f'Geçersiz veri tipi: {field} string olmalıdır.', 'status': 'error'}, status=400)

    for field in ['IletisimList', 'IletisimList_Birey']:
        value = data.get(field)
        if value is not None and not isinstance(value, list):
            return False, JsonResponse({'message': f'Geçersiz veri tipi: {field} liste olmalıdır.', 'status': 'error'}, status=400)

    return True, None


def add_vpos_transation(data):
    company = Company.objects.filter(uuid = data.get('CompanyId')).first()
    
    process_date = parse_datetime(data.get('ProcessDate'))
        
    currency = Currency.objects.filter(code='TRY' if data.get('CurrencyCode') == 'TL' else data.get('CurrencyCode')).first()

    cleared_data = {k: v for k, v in data.items() if v != ""}

    obj = VPosTransaction.objects.create(
        company = company,
        source = data.get('ValidationKey') == settings.VPOS_VALIDATION_KEY_APP if Sources.APP else Sources.WEB,
        payload = cleared_data,
        status = Statuses.PENDING,    
        process_date = process_date,
        musteri_tipi = data.get('MusteriTipi'),
        paid_amount = safe_decimal(data.get('PaidAmount')),
        currency = currency,
        lease_posting_group_id = data.get('LeasePostingGroupId'),

        firma_adi = data.get('FirmaAdi'),
        kurum_tipi = data.get('KurumTipi'),
        vergi_dairesi = data.get('VergiDairesi'),
        vergi_no = data.get('VergiNo'),
        web_sitesi = data.get('WebSitesi'),
        adres = data.get('Adres'),
        ulke = data.get('Ulke'),
        sehir = data.get('Sehir'),
        ilce = data.get('Ilce'),
        posta = data.get('Posta'),

        kart_sahibi_ad_soyad = data.get('KartAdSoyad'),
        ad = data.get('Ad'),
        ikinci_ad = data.get('IkinciAd'),
        orta_ad = data.get('OrtaAd'),
        soyad = data.get('SoyAd'),
        cinsiyet = data.get('Cinsiyet'),
        tc_kimlik_no = data.get('TCKimlikNo'),
        pasaport_no = data.get('PasaportNo'),
        uyruk = data.get('Uyruk'),
        dogum_tarihi = data.get('DogumTarih'),
        vergi_dairesi_birey = data.get('VergiDairesi_Birey'),
        vergi_no_birey = data.get('VergiNo_Birey'),
        adres_birey = data.get('Adres_Birey'),
        ulke_birey = data.get('Ulke_Birey'),
        sehir_birey = data.get('Sehir_Birey'),
        ilce_birey = data.get('Ilce_Birey'),
        posta_birey = data.get('Posta_Birey'),

        username = data.get('UserName'),
        telefon = data.get('Telefon'),
        email = data.get('EMail'),
        fax = data.get('Fax'),
        bank_code = data.get('BankCode'),
        contract_code = data.get('ContractCode'),
        ext_transaction_id = data.get('ExtTransactionId'),
    )

    if len(data.get('IletisimList') or []) > 0 or len(data.get('IletisimList_Birey') or []) > 0:
        iletisim_list = data.get('IletisimList') or data.get('IletisimList_Birey')
        for iletisim in iletisim_list:
            VPosIletisim.objects.create(
                vpos_transaction = obj,
                company = obj.company,
                iletisim_turu = iletisim.get('IletisimTuru'),
                iletisim_degeri = iletisim.get('IletisimDegeri'),
            )

    # third_person_result = compare_names(isim=data.get('Ad'), soyisim=data.get('SoyAd'), kart_sahibi=data.get('KartAdSoyad'))

    # if third_person_result == NameMatch.MATCH:
    #     print("Aynı kişi: Ad ve Soyad ile Kart Ad Soyad eşleşiyor.")
    # elif third_person_result == NameMatch.REVIEW:
    #     print("İnceleme gerekli: Ad ve Soyad ile Kart Ad Soyad benzer ama tam olarak eşleşmiyor.")
    #     scan_result = check_third_person_status_vpos(data.get('KartAdSoyad'))
    #     create_third_person_vpos(obj,scan_result)
    # else:
    #     print("Farklı kişi: Ad ve Soyad ile Kart Ad Soyad eşleşmiyor.")
    #     scan_result = check_third_person_status_vpos(data.get('KartAdSoyad'))
    #     create_third_person_vpos(obj,scan_result)

    

    return obj

def send_vpos_transation_to_leaseflex(uuid):
    WSDL = "https://leaseflex.arileasing.com.tr/ARI_LEASING/Integration/Collection/VirtualPosIntegrationService.asmx?WSDL"
    
    session = requests.Session()
    transport = Transport(session=session, timeout=30)
    history = HistoryPlugin()
    client = Client(wsdl=WSDL, transport=transport, plugins=[history])

    add_collection = client.get_element("{http://tempuri.org/}AddCollection")
    request_type = dict(add_collection.type.elements)["request"].type
    allowed = {name for name, _ in request_type.elements}

    with transaction.atomic():
        obj = (
            VPosTransaction.objects.select_for_update(skip_locked=True, of=("self",))
            .select_related("currency")
            .filter(uuid=uuid)
            .first()
        )

        if obj is None or obj.status != Statuses.PENDING:
            return False, f'VPosTransaction with UUID {uuid} not found or not in PENDING status'

        request = {k: v for k, v in obj.payload.items() if k in allowed and v not in (None, "")}

        for key in ("IletisimList", "IletisimList_Birey"):
            if isinstance(request.get(key), list):
                request[key] = {"Iletisim": request[key]}

        # Tutarı float yerine 2 haneli Decimal olarak gönder
        request["PaidAmount"] = Decimal(str(request["PaidAmount"])).quantize(Decimal("0.01"))

        # Kimlik bilgisi payload'dan değil, settings'ten
        request["UserName"] = settings.ARI_VPOS_USERNAME
        request["Password"] = settings.ARI_VPOS_PASSWORD

        response = client.service.AddCollection(request=request)

    return response.Result, response.Message

def send_vpos_transation_to_leaseflex_test(uuid):
    WSDL = "https://testleaseflex.arileasing.com.tr/ARI_LEASING/Integration/Collection/VirtualPosIntegrationService.asmx?WSDL"
    
    session = requests.Session()
    transport = Transport(session=session, timeout=30)
    history = HistoryPlugin()
    client = Client(wsdl=WSDL, transport=transport, plugins=[history])

    add_collection = client.get_element("{http://tempuri.org/}AddCollection")
    request_type = dict(add_collection.type.elements)["request"].type
    allowed = {name for name, _ in request_type.elements}

    with transaction.atomic():
        obj = (
            VPosTransaction.objects.select_for_update(skip_locked=True, of=("self",))
            .select_related("currency")
            .filter(uuid=uuid)
            .first()
        )

        if obj is None or obj.status != Statuses.PENDING:
            return False, f'VPosTransaction with UUID {uuid} not found or not in PENDING status'

        request = {k: v for k, v in obj.payload.items() if k in allowed and v not in (None, "")}

        for key in ("IletisimList", "IletisimList_Birey"):
            if isinstance(request.get(key), list):
                request[key] = {"Iletisim": request[key]}

        # Tutarı float yerine 2 haneli Decimal olarak gönder
        request["PaidAmount"] = Decimal(str(request["PaidAmount"])).quantize(Decimal("0.01"))

        # Kimlik bilgisi payload'dan değil, settings'ten
        request["UserName"] = settings.ARI_VPOS_USERNAME
        request["Password"] = settings.ARI_VPOS_PASSWORD

        response = client.service.AddCollection(request=request)

    return response.Result, response.Message

    # for service in client.wsdl.services.values():
    #     for port in service.ports.values():
    #         operations = port.binding._operations
    #         for op_name in operations:
    #             print(op_name)

    # result = client.service.Test()