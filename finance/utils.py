from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value

import requests
from datetime import datetime,date,timedelta
import pandas as pd
import io
from decimal import Decimal, InvalidOperation
import re
import os
import random
import string

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


def finmaks_encrypt_password(PASSWORD):
    url = "http://finmaks.arileasing.com.tr:92/EncryptPass"
    payload = {"Pass": PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, params=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("Message")
    else:
        return response.text
    
def fetch_finmaks_bank_accounts(USERNAME,PASSWORD,INSTITUTION_CODE,INSTITUTION_ID,BANK_INTEGRATION_INFO_ID="",BANK_CODE=""):
    encrypted_password = finmaks_encrypt_password(PASSWORD)


    url = "http://finmaks.arileasing.com.tr:92/BankAccounts"
    payload = {
        "username": USERNAME,
        "password": encrypted_password,
        "institutionCode": INSTITUTION_CODE,
        "institutionId": INSTITUTION_ID
    }
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, params=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("InstitutionBankAccounts")
    else:
        return response.text
    
def fetch_finmaks_transactions(USERNAME,PASSWORD,INSTITUTION_CODE,INSTITUTION_ID,BANK_INTEGRATION_INFO_ID="",BANK_CODE=""):
    encrypted_password = finmaks_encrypt_password(PASSWORD)


    url = "http://finmaks.arileasing.com.tr:92/Transactions"
    payload = {
        "username": USERNAME,
        "password": encrypted_password,
        "institutionCode": INSTITUTION_CODE,
        "institutionId": INSTITUTION_ID
    }
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, params=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("BankTransactionList")
    else:
        return response.text
    
