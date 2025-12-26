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

from .models import *
from common.models import Currency, ExchangeRate

def is_valid_finmaks_transaction_data(data):
    if not data.get('bank_account') or not data.get('transaction_date'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def vendor_filter_for_serializers(filter_params):
    if filter_params.get('project') == "all":
        return Q()
    elif filter_params.get('project') == "diger":
        return (
            ~Q(lease__contract__vendor__crm_code__in=["11802","20559","1202","28974","6548"]) &
            ~Q(lease__contract__vendor__crm_code__in=["1202"]) &
            ~Q(lease__contract__project="SAKLI KORU KONAKLARI") &
            ~Q(lease__contract__project="SİNPAŞ KORU AURA") &
            ~Q(lease__contract__project="SİNPAŞ TABİAT VİLLALARI") &
            ~Q(lease__contract__project="METROLİFE PREMİUM") &
            ~Q(lease__contract__project="METROLİFE") &
            ~Q(lease__contract__project="METROLIFE PREMİUM") &
            ~Q(lease__contract__project="METROLIFE") &
            ~Q(lease__contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT") &
            ~Q(lease__contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT-") &
            ~Q(lease__contract__project="BOULEVARD SEFAKÖY")
        )
    elif filter_params.get('project') == "kizilbuk":
        return Q(lease__contract__vendor__crm_code__in=["11802","20559"])
    elif filter_params.get('project') == "sinpas":
        return (
            Q(lease__contract__vendor__crm_code__in=["1202"]) |
            Q(lease__contract__project="SAKLI KORU KONAKLARI") |
            Q(lease__contract__project="SİNPAŞ KORU AURA") |
            Q(lease__contract__project="SİNPAŞ TABİAT VİLLALARI") |
            Q(lease__contract__project="METROLİFE PREMİUM") |
            Q(lease__contract__project="METROLİFE") |
            Q(lease__contract__project="METROLIFE PREMİUM") |
            Q(lease__contract__project="METROLIFE")
        )
    elif filter_params.get('project') == "kasaba":
        return (
            Q(lease__contract__vendor__crm_code__in=["28974"]) |
            Q(lease__contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT") |
            Q(lease__contract__project="SİNPAŞ KASABA THERMAL WELLNESS RESORT-")
        )
    elif filter_params.get('project') == "servet":
        return (
            (
                Q(lease__contract__vendor__crm_code__in=["6548","6546"]) |
                Q(lease__contract__project="BOULEVARD SEFAKÖY")
            ) &
            ~Q(lease__contract__project="SİNPAŞ KORU AURA")
        )
    else:
        return Q(lease__contract__vendor__crm_code=filter_params.get('project'))


def finmaks_encrypt_password():
    url = "http://finmaks.arileasing.com.tr:92/EncryptPass"
    payload = {"Pass": settings.FINMAKS_PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, params=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("Message")
    else:
        return response.text
    
def get_finmaks_bank_accounts():
    encrypted_password = finmaks_encrypt_password()

    url = "http://finmaks.arileasing.com.tr:92/BankAccounts"
    payload = {
        "username": settings.FINMAKS_USERNAME,
        "password": encrypted_password,
        "institutionCode": settings.FINMAKS_INSTITUTION_CODE,
        "institutionId": settings.FINMAKS_INSTITUTION_ID
    }
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, params=payload, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json().get("InstitutionBankAccounts")}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
    
    
def get_finmaks_transactions():
    encrypted_password = finmaks_encrypt_password()

    url = "http://finmaks.arileasing.com.tr:92/Transactions"
    payload = {
        "username": settings.FINMAKS_USERNAME,
        "password": encrypted_password,
        "institutionCode": settings.FINMAKS_INSTITUTION_CODE,
        "institutionId": settings.FINMAKS_INSTITUTION_ID
    }
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, params=payload, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json().get("BankTransactionList")}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def fetch_finekra_token():
    url = "https://finekra-api.sinpas.com.tr/api/Auth/DealerLogin"
    payload = {
        "email": str(os.getenv("FINEKRA_USERNAME")),
        "password": str(os.getenv("FINEKRA_PASSWORD")),
        "tenantCode": str(os.getenv("FINEKRA_TENANT_CODE")),
        "screenOption": int(os.getenv("FINEKRA_SCREEN_OPTION"))
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()['data']['token']
    else:
        return response.text

def fetch_finekra_banks():
    token = fetch_finekra_token()

    url = "https://finekra-api.sinpas.com.tr/api/Bank"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()['value']
    else:
        return []
    
def fetch_finekra_currencies():
    token = fetch_finekra_token()

    url = "https://finekra-api.sinpas.com.tr/api/Currency"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()['value']
    else:
        return []
    
def fetch_finekra_bank_accounts():
    token = fetch_finekra_token()

    url = "https://finekra-api.sinpas.com.tr/api/TenantAccount"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
			"$count": "true",
			"$skip": "0",
			"$top": "100"
		}
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()['value']
    else:
        return []
    
def post_finekra_bank_accounts(data):
    token = fetch_finekra_token()

    url = "https://finekra-api.sinpas.com.tr/api/TenantAccount/TenantAccountRegister"
    payload = {
        "iban": data["iban"],
        "balance": data["balance"],
        "branchCode": data["branchCode"],
        "branchName": data["branchName"],
        "accountNumber": data["accountNumber"],
        "accountSuffix": data["accountSuffix"],
        "currencyId": data["currencyId"],
        "description": data["description"],
        "name": data["name"],
        "type": data["type"],
        "dueDate": data["dueDate"],
        "interestRate": data["interestRate"],
        "isCalculated": data["isCalculated"],
        "bankId": data["bankId"],
        "creditLimit": data["creditLimit"],
        "lastQueryDate": data["lastQueryDate"],
        "availableCreditLimit": data["availableCreditLimit"],
        "availableCreditBalance": data["availableCreditBalance"],
        "availableBalance": data["availableBalance"],
        "openDate": data["openDate"],
        "creditBalance": data["creditBalance"],
        "blockedAmount": data["blockedAmount"],
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()["data"]["id"]}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def put_finekra_bank_accounts(data):
    token = fetch_finekra_token()

    url = "https://finekra-api.sinpas.com.tr/api/TenantAccount/UpdateTenantAccount"
    payload = {
        "id": data["id"],
        "balance": data["balance"],
        "availableCreditBalance": data["availableCreditBalance"],
        "availableBalance": data["availableBalance"],
        "blockedAmount": data["blockedAmount"],
    }
    payload2 = {
        "id": data["id"],
        "iban": data["iban"],
        "balance": data["balance"],
        "branchCode": data["branchCode"],
        "branchName": data["branchName"],
        "accountNumber": data["accountNumber"],
        "accountSuffix": data["accountSuffix"],
        "currencyId": data["currencyId"],
        "description": data["description"],
        "name": data["name"],
        "type": data["type"],
        "dueDate": data["dueDate"],
        "interestRate": data["interestRate"],
        "isCalculated": data["isCalculated"],
        "bankId": data["bankId"],
        "creditLimit": data["creditLimit"],
        "lastQueryDate": data["lastQueryDate"],
        "availableCreditLimit": data["availableCreditLimit"],
        "availableCreditBalance": data["availableCreditBalance"],
        "availableBalance": data["availableBalance"],
        "openDate": data["openDate"],
        "creditBalance": data["creditBalance"],
        "blockedAmount": data["blockedAmount"],
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.put(url, json=payload2, headers=headers)

    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def delete_finekra_bank_account(id):
    token = fetch_finekra_token()

    url = f"https://finekra-api.sinpas.com.tr/api/TenantAccount/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(url, headers=headers)

    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def export_finmaks_bank_account_balances(self):
    queryset = FinmaksBankAccount.objects.select_related().filter()

    self.process.status = "in_progress"
    self.process.items_count = len(queryset)
    self.process.save()

    previous_progress = 0

    if self.params.get('date'):
        params_date = self.params.get('date')
    else:
        params_date = localtime().date()

    usd_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="USD",date=params_date).first().forex_buying
    eur_exchange_rate = ExchangeRate.objects.filter(target_currency__code ="EUR",date=params_date).first().forex_buying

    current_progress = 15

    if current_progress - previous_progress >= 5:
        self.process.progress = int(current_progress)
        self.process.save()
        previous_progress = current_progress

    result = {
        'active_balances' : {
            'try_balance': queryset.filter(currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
            'usd_balance': queryset.filter(currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
            'usd_try_balance': (queryset.filter(currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * usd_exchange_rate,
            'eur_balance': queryset.filter(currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00'),
            'eur_try_balance': (queryset.filter(currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * eur_exchange_rate,
            'total_try_balance': (queryset.filter(currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) + ((queryset.filter(currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * usd_exchange_rate) + ((queryset.filter(currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')) * eur_exchange_rate),
        },
        'bank_accounts' : {
            'yapi_kredi': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0067', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance': queryset.filter(bank_code='0067', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')
                }],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0067', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0067', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')
                }],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0067', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0067', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'albaraka': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0203', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0203', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0203', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0203', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0203', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0203', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'vakifbank': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0015', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0015', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0015', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0015', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0015', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0015', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'vakif_katilim': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0210', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0210', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0210', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0210', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0210', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0210', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'akbank': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0046', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0046', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0046', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0046', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0046', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0046', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'is_bank': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0064', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0064', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'garanti': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='9999', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='9999', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='9999', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='9999', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='9999', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='9999', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'halkbank': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0012', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0012', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0012', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0012', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0012', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0012', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'ziraat': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0010', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0010', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0010', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0010', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0010', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0010', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'ziraat_katilim': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0209', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0209', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0209', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0209', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0209', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0209', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'turkiye_finans': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0206', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0206', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0206', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0206', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0206', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0206', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'teb': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='8888', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='8888', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'kuveytturk': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='0205', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='0205', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
            'emlak_katilim': {
                'try' : [{
                    'id':obj.id,
                    'account_no':  f"TRY - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='7777', currency__code='TRY')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='7777', currency__code='TRY').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'usd' : [{
                    'id':obj.id,
                    'account_no':  f"USD - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='7777', currency__code='USD')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='7777', currency__code='USD').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
                'eur' : [{
                    'id':obj.id,
                    'account_no':  f"EUR - {obj.account_no}",
                    # 'iban': obj.iban,
                    'balance': obj.available_balance} for obj in queryset.filter(bank_code='7777', currency__code='EUR')] + [{'id':'999','account_no':'TOPLAM','balance':queryset.filter(bank_code='7777', currency__code='EUR').aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')}],
            },
        },
        'exchange_rates' : {
            'usd_exchange_rate': usd_exchange_rate,
            'eur_exchange_rate': eur_exchange_rate,
        }
    }
    
    # TOPLAM KULLANILABİLİR BAKİYELER
    formatted_date = params_date.strftime("%d.%m.%Y") if isinstance(params_date, (datetime, date)) else datetime.strptime(str(params_date), "%Y-%m-%d").strftime("%d.%m.%Y")
    data_active_balances = {
        "KULLANILABİLİR BAKİYE TOPLAMLARI": [],
        f"{formatted_date}": [],
    }

    data_active_balances["KULLANILABİLİR BAKİYE TOPLAMLARI"].append('TOPLAM TRY BAKİYE')
    data_active_balances[f"{formatted_date}"].append(result['active_balances']['try_balance'])

    data_active_balances["KULLANILABİLİR BAKİYE TOPLAMLARI"].append('TOPLAM USD BAKİYE')
    data_active_balances[f"{formatted_date}"].append(result['active_balances']['usd_balance'])

    data_active_balances["KULLANILABİLİR BAKİYE TOPLAMLARI"].append('TOPLAM USD/TRY BAKİYE')
    data_active_balances[f"{formatted_date}"].append(result['active_balances']['usd_try_balance'])

    data_active_balances["KULLANILABİLİR BAKİYE TOPLAMLARI"].append('TOPLAM EUR BAKİYE')
    data_active_balances[f"{formatted_date}"].append(result['active_balances']['eur_balance'])

    data_active_balances["KULLANILABİLİR BAKİYE TOPLAMLARI"].append('TOPLAM EUR/TRY BAKİYE')
    data_active_balances[f"{formatted_date}"].append(result['active_balances']['eur_try_balance'])

    data_active_balances["KULLANILABİLİR BAKİYE TOPLAMLARI"].append('GENEL TOPLAM TRY BAKİYE')
    data_active_balances[f"{formatted_date}"].append(result['active_balances']['total_try_balance'])

    df_active_balances = pd.DataFrame(data_active_balances)
    df_active_balances = df_active_balances.drop_duplicates()

    numeric_columns = [
        f"{formatted_date}"
    ]

    for col in numeric_columns:
        df_active_balances[col] = pd.to_numeric(df_active_balances[col], errors="coerce")

    # BANKA BAKİYELERİ - YAPI KREDİ
    data_active_balances = {
        "YAPI KREDİ": [],
        f"{formatted_date}": [],
    }

    
    base_path = os.path.join(os.getcwd(), "media", "docs", str(self.user.user_companies.filter(is_active=True).first().company.uuid), "finance", "finmaks_bank_account_balances", "documents")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    excel_dosyasi_adi = f"{base_path}/{datetime.today().strftime('%d-%m-%Y')}-banka-bakiyeleri.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
        df_active_balances.to_excel(writer, sheet_name='Sayfa', index=False)

        # Workbook'u al
        workbook = writer.book
        worksheet = writer.sheets['Sayfa']

        # Kolon isimlerine göre format uygula
        for idx, col in enumerate(df_active_balances.columns, 1):  # enumerate 1'den başlıyor
            if col in numeric_columns:
                for cell in worksheet.iter_cols(min_col=idx, max_col=idx, min_row=2):
                    for c in cell:
                        c.number_format = '#,##0.00'   # İstediğin format
        
    self.process.progress = 100
    #self.process.status = "completed"
    self.process.save()