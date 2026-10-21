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

from finance.models import *
from common.models import Currency, ExchangeRate
from common.utils.common_utils import parse_datetime,safe_decimal

def is_valid_vpos_transaction_data(data):
    parameters = [
        'CompanyId', 'ValidationKey', 'ProcessDate', 'MusteriTipi', 'PaidAmount',
        'LeasePostingGroupId', 'FirmaAdi', 'KurumTipi', 'VergiDairesi', 'VergiNo',
        'WebSitesi', 'Adres', 'Ulke', 'Sehir', 'Ilce', 'Posta', 'IletisimList',
        'Ad', 'IkinciAd', 'OrtaAd', 'SoyAd', 'Cinsiyet', 'TCKimlikNo', 'PasaportNo',
        'Uyruk', 'DogumTarih', 'VergiDairesi_Birey', 'VergiNo_Birey', 'Adres_Birey',
        'Ulke_Birey', 'Sehir_Birey', 'Ilce_Birey', 'Posta_Birey', 'IletisimList_Birey',
        'UserName', 'Password', 'Telefon', 'EMail', 'Fax', 'BankCode', 'ContractCode',
        'CurrencyCode', 'ExtTransactionId',
    ]

    unknown_keys = set(data.keys()) - set(parameters)
    if unknown_keys:
        return False, JsonResponse({'message': f'Geçersiz parametre(ler): {", ".join(sorted(unknown_keys))}', 'status': 'error'}, status=400)

    if not data.get('CompanyId') or not Company.objects.filter(uuid=data.get('CompanyId')).exists():
        return False, JsonResponse({'message': 'Şirket bilgisi eksik veya geçersiz! (CompanyId)','status':'error'}, status=400)
    
    if not data.get('ValidationKey') or data.get('ValidationKey') != settings.VPOS_VALIDATION_KEY:
        return False, JsonResponse({'message': 'Doğrulama anahtarı geçersiz! (ValidationKey)','status':'error'}, status=400)
    
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

    str_fields = [
        'FirmaAdi', 'KurumTipi', 'VergiDairesi', 'VergiNo', 'WebSitesi',
        'Adres', 'Ulke', 'Sehir', 'Ilce', 'Posta',
        'Ad', 'IkinciAd', 'OrtaAd', 'SoyAd', 'Cinsiyet',
        'TCKimlikNo', 'PasaportNo', 'Uyruk', 'DogumTarih',
        'VergiDairesi_Birey', 'VergiNo_Birey', 'Adres_Birey',
        'Ulke_Birey', 'Sehir_Birey', 'Ilce_Birey', 'Posta_Birey',
        'UserName', 'Password', 'Telefon', 'EMail', 'Fax',
        'BankCode', 'ContractCode', 'ExtTransactionId',
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

    obj = VPosTransaction.objects.create(
        company = company,
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

        kart_sahibi_ad_soyad = data.get('KartSahibiAdSoyad'),
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