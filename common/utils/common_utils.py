from unidecode import unidecode
from decimal import Decimal,InvalidOperation

def normalize(name):
    return unidecode(name or "").strip().lower()

def safe_decimal(val, default="0"):
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)