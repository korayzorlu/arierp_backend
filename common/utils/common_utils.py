from unidecode import unidecode
from decimal import Decimal,InvalidOperation
from datetime import timedelta
import requests
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import traceback
import time
import re

def normalize(name):
    return unidecode(name or "").strip().lower()

def safe_decimal(val, default="0"):
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)

def has_more_than_two_decimal_places(val):
    dec = safe_decimal(val)
    # dec.as_tuple().exponent negatifse, ondalık basamak sayısı -exponent olur
    return abs(dec.as_tuple().exponent) > 2
    
def parse_amount(amount_str):
    """
    Farklı yazım türlerinde verilen para tutarını normalize ederek float'a çevirir.
    """
    if not amount_str:
        return Decimal('0.00')

    # Remove all non-digit/decimal chars except ',' and '.'
    amount_str = str(amount_str).strip()

    # Eğer her iki karakter de varsa:
    if "," in amount_str and "." in amount_str:
        # Sondaki ayırıcı , ise bu Avrupa formatıdır: 19.731,25 → 19731.25
        if amount_str.rfind(",") > amount_str.rfind("."):
            amount_str = amount_str.replace(".", "").replace(",", ".")
        # Sondaki ayırıcı . ise bu Amerikan formatıdır: 19,731.25 → 19731.25
        else:
            amount_str = amount_str.replace(",", "")
    elif "," in amount_str:
        # Virgül varsa ve nokta yoksa, bu Avrupa formatıdır: 19731,25 → 19731.25
        amount_str = amount_str.replace(".", "").replace(",", ".")
    else:
        # Sadece nokta varsa: 19731.25 → olduğu gibi
        amount_str = amount_str.replace(",", "")  # yine de temizlik

    try:
        return Decimal(amount_str)
    except:
        return Decimal('0.00')  # fallback
    
def add_business_days(start_date, business_days):
    current_date = start_date
    days_added = 0

    while days_added < business_days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:
            days_added += 1

    return current_date

def get_exchange_rate_for_date(target_currency=None, date=None):
    try:
        start_date = datetime.now() - timedelta(days=365*10)
        end_date = datetime.now()

        current_date = start_date
        # while current_date <= end_date:
        #     # Burada current_date kullanılabilir
        #     #print(f"{current_date.strftime("%Y%m")} - {current_date.strftime("%d%m%Y")}")
        #     current_date += timedelta(days=1)
        
        # date örneği: "11-09-2025"
        # URL formatı: https://www.tcmb.gov.tr/kurlar/YYYYMM/DDMMYYYY.xml
        if date:
            dt = datetime.strptime(date, "%d-%m-%Y")
        else:
            dt = datetime.now()

        if dt.day == 1 and dt.month == 1:  # Yeni yılın ilk günü
            dt -= timedelta(days=1)
            time.sleep(0.1)
        elif dt.weekday() == 5:  # Cumartesi
            dt -= timedelta(days=1)
            if dt.day == 1 and dt.month == 1:
                dt -= timedelta(days=1)
            time.sleep(0.1)
        elif dt.weekday() == 6:  # Pazar
            dt -= timedelta(days=2)
            if dt.day == 1 and dt.month == 1:
                dt -= timedelta(days=1)
            time.sleep(0.1)

        url = f"https://www.tcmb.gov.tr/kurlar/{dt.strftime('%Y%m')}/{dt.strftime('%d%m%Y')}.xml"
        response = requests.get(url)
        
        root = ET.fromstring(response.content)

        currencies = []
        for currency in root.findall("Currency"):
            data = {
                # "CrossOrder": currency.get("CrossOrder"),
                "Kod": currency.get("Kod"),
                # "CurrencyCode": currency.get("CurrencyCode"),
                # "Unit": currency.findtext("Unit"),
                # "Isim": currency.findtext("Isim"),
                # "CurrencyName": currency.findtext("CurrencyName"),
                "ForexBuying": currency.findtext("ForexBuying"),
                "ForexSelling": currency.findtext("ForexSelling"),
                # "BanknoteBuying": currency.findtext("BanknoteBuying"),
                # "BanknoteSelling": currency.findtext("BanknoteSelling"),
                # "CrossRateUSD": currency.findtext("CrossRateUSD"),
                # "CrossRateOther": currency.findtext("CrossRateOther"),
            }
            currencies.append(data)

        # data_json = json.dumps(currencies, ensure_ascii=False, indent=2)

        result = next((item for item in currencies if item["Kod"] == target_currency), None)

        return {
            "date": date,
            "forex_buying": Decimal(str(result["ForexBuying"])) if result else Decimal('0.00'),
            "forex_selling": Decimal(str(result["ForexSelling"])) if result else Decimal('0.00'),
        }
    except Exception as e:
        print("Error in get_exhange_rate_for_date:", str(e))
        traceback.print_exc()
        return {
            "date": date,
            "forex_buying": Decimal('0.00'),
            "forex_selling": Decimal('0.00'),
        }

def catch_name_from_description(self):
    if self.finmaks_transaction.bank_account.account_no == '00158007306261159': # vakıf try
        if re.search(r"\bhesabından\b", self.description):
            catched_name = re.search(r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)\s+hesabından", self.description)
        elif re.search(r"\btarafından\b", self.description):
            catched_name = re.search(r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)\s+tarafından", self.description)
        else:
            catched_name = None
    # elif self.finmaks_transaction.bank_account.account_no == '00158048012388185': # vakıf usd
    #     catched_name = re.search(r"-\s*(.*?)\s*-", self.description)
    elif self.finmaks_transaction.bank_account.account_no == '9626-07427880-10100981': # halk try
        pattern = re.compile(r"^(.+?)\s+\1\b", re.IGNORECASE)
        catched_name = pattern.match(self.description)
    elif self.finmaks_transaction.bank_account.bank_code == '0067': # yapı kredi hepsi
        catched_name = re.search(r"-\s*(.*?)\s*-", self.description)
    else:
        catched_name = None

    if catched_name:
        name = catched_name.group(1)
    else:
        name = None

    return name

def catch_name_from_finmaks_transaction(self):
    if self.bank_account.account_no == '00158007306261159' or self.bank_account.account_no == '001580480123881851': # vakıf
        if re.search(r"\bhesabından\b", self.explanation_field):
            catched_name = re.search(r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)\s+hesabından", self.explanation_field)
        elif re.search(r"\btarafından\b", self.explanation_field):
            catched_name = re.search(r"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+?)\s+tarafından", self.explanation_field)
        else:
            catched_name = None
    # elif self.bank_account.account_no == '00158048012388185': # vakıf usd
    #     catched_name = re.search(r"-\s*(.*?)\s*-", self.explanation_field)
    elif self.bank_account.account_no == '9626-07427880-10100981': # halk try
        pattern = re.compile(r"^(.+?)\s+\1\b", re.IGNORECASE)
        catched_name = pattern.match(self.explanation_field)
    elif self.bank_account.bank_code == '0067': # yapı kredi hepsi
        print(re.search(r"-\s*(.*?)\s*-", self.explanation_field))
        catched_name = re.search(r"-\s*(.*?)\s*-", self.explanation_field)
    else:
        catched_name = None

    if catched_name:
        name = catched_name.group(1)
    else:
        name = None
    print(name)
    return name