from unidecode import unidecode
from decimal import Decimal,InvalidOperation
from datetime import timedelta

def normalize(name):
    return unidecode(name or "").strip().lower()

def safe_decimal(val, default="0"):
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)
    
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