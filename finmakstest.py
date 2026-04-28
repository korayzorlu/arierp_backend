from django.conf import settings

import requests
import datetime
import os
import django

from decouple import config

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# FinMaks API URL
BASE_URL = "http://finmaks.arileasing.com.tr:92"  # Dokümanda varsa doğru URL ile değiştir
ENCRYPT_PASS_ENDPOINT = "/EncryptPass"
TRANSACTIONS_ENDPOINT = "/Transactions"

# Kullanıcı bilgileri
USERNAME = settings.FINMAKS_USERNAME
PASSWORD = settings.FINMAKS_PASSWORD

INSTITUTION_CODE = "0001"
INSTITUTION_ID = 1  # Kurum ID'nizi girin
BANK_CODE = "0046"  # TCMB banka kodu
START_DATE = "2025-08-01"
END_DATE = "2025-08-31"

# 1. Şifreyi Encrypt Et
def encrypt_password():
    url = BASE_URL + ENCRYPT_PASS_ENDPOINT
    payload = {"Pass": PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("Message")  # Dokümana göre "Message" döner
    else:
        raise Exception(f"EncryptPass Hatası: {response.text}")

# 2. Hesap Hareketlerini Getir
def get_transactions():
    encrypted_password = encrypt_password()

    url = BASE_URL + TRANSACTIONS_ENDPOINT
    headers = {"Content-Type": "application/json"}
    payload = {
        "SecurityData": {
            "Username": USERNAME, 
            "Password": encrypted_password,
            "InstitutionCode": INSTITUTION_CODE
        },
        "InstitutionId": INSTITUTION_ID,
        "BankCode": BANK_CODE,
        "StartDate": START_DATE,
        "EndDate": END_DATE
    }

    response = requests.get(url, params=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("✅ Hesap hareketleri başarıyla alındı!")
        return data
    else:
        print("❌ Hata:", response.status_code, response.text)
        return None

# Çalıştır
transactions = get_transactions()

if transactions:
    for tx in transactions.get("Transactions", []):
        print(f"{tx['TransactionDate']} - {tx['Description']} - {tx['Amount']} {tx['Currency']}")