from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings

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



def get_turatel_credit():
    url = "https://api.turatel.com/AllInOneWebService/json-api/api/SmsProxy/getCredit"
    payload = {
        "username": "otparileasing",
        "password": "3k9kW6hU4",
        "userCode": 2678,
        "accountId": 2093
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def get_turatel_originator():
    url = "https://api.turatel.com/AllInOneWebService/json-api/api/SmsProxy/getOriginator"
    payload = {
        "username": "otparileasing",
        "password": "3k9kW6hU4",
        "userCode": 2678,
        "accountId": 2093
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def get_turatel_status(data=None):
    url = "https://api.turatel.com/AllInOneWebService/json-api/api/SmsProxy/getStatus"
    payload = {
        "packetId": data.get("packetId", ""),
        "username": "otparileasing",
        "password": "3k9kW6hU4",
        "userCode": 2678,
        "accountId": 2093
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    
def send_turatel_sms(data=None):
    url = "https://api.turatel.com/AllInOneWebService/json-api/api/SmsProxy/sendSMS"
    payload = {
        "username": "otparileasing",
        "password": "3k9kW6hU4",
        "userCode": 2678,
        "accountId": 2093,
        "originator": "ARIFINANSAL",
        "validityPeriod": 0,
        "isCheckBlackList": True,
        "isEncryptedParameter": True,
        "referenceId":"1",
        "sendDate": "",
        "messageText": data.get("messageText", ""),
        "receiverList": data.get("receiverList", []),
        "personalMessages": data.get("personalMessages", []),
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return {"status": "success", "status_code": 200, "message": response.json()}
    else:
        return {"status": "error", "status_code": response.status_code, "message": response.text}
    