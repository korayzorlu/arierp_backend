from unidecode import unidecode

def normalize(name):
    return unidecode(name or "").strip().lower()