import requests

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