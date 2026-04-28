from django.test import TestCase
import re

# Create your tests here.from decimal import Decimal, ROUND_HALF_UP
#from .models import Installment

# installments = Installment.objects.select_related("lease").all()
# installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency}
# obj = (installment_by_code.get(("91556",0)))

# print(obj)



# import requests
# from requests.auth import HTTPBasicAuth

# # API kullanıcı bilgileri
# USERNAME = "ae3b6b57-bdf8-4e79-84ad-3adf2eb4d713"
# PASSWORD = "2ig#ufok$1"

# # Aranacak isim ve isteğe bağlı parametreler
# params = {
#     "id": "48856880254",     # en az 3 karakter
#     "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
#     "start": 0,                 # sayfalama başlangıcı
#     "limit": 20,                # maksimum 50
#     #"birthYear": "1980",
#     "minMatchRate": 95,
#     "isDeepSearch": True
# }

# response = requests.get(
#     "https://api.sanctionscanner.com/api/Search/SearchByIdentity",
#     params=params,
#     auth=HTTPBasicAuth(USERNAME, PASSWORD)
# ).json()

# for item in response["Result"]["Result"]:
#     print(f"FullName: {item["FullName"]} |MatchRate: {item["MatchRate"]} | Type: {item["Type"]} | ")


# print(f"Temiz mi?: {"Temiz" if len(response["Result"]["Result"]) == 0 else "Sorunlu"} | Pep mi?: ")


def extract_contract_numbers(description):
    matches = []
    
    # normal yazılmış numaralar
    normal_numbers = re.findall(r'\b\d{4,5}\b', description.lower())
    for number in normal_numbers:
        if number not in matches and number not in ['2024', '2025', '2023']:
            matches.append(number)

    #nokta ile ayrılmış numaralar
    dot_numbers = re.findall(r'\b\d{1,2}.\d{3,4}\b', description.lower())
    for number in dot_numbers:
        if number not in matches:
            matches.append(number.replace('.',''))

    #/ ile ayrılmış numaralar
    slash_numbers = re.findall(r'\b\d{4,5}/\d{1,2}\b', description.lower())
    for number in slash_numbers:
        if number not in matches:
            matches.append(number)

    # temizlenmiş ve tekrar edenlerden arındırılmış numaralar
    result = []
    seen = set()
    for match in matches:
        match = match.strip()
        if (re.fullmatch(r'\d{4,5}', match) or re.fullmatch(r'\d{4,5}/\d{1,2}', match)) and match not in seen:
            result.append(match)
            seen.add(match)

    return result
