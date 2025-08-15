from django.test import TestCase

# Create your tests here.from decimal import Decimal, ROUND_HALF_UP
#from .models import Installment

# installments = Installment.objects.select_related("lease").all()
# installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency}
# obj = (installment_by_code.get(("91556",0)))

# print(obj)



import requests
from requests.auth import HTTPBasicAuth

# API kullanıcı bilgileri
USERNAME = "ae3b6b57-bdf8-4e79-84ad-3adf2eb4d713"
PASSWORD = "2ig#ufok$1"

# Aranacak isim ve isteğe bağlı parametreler
params = {
    "id": "48856880254",     # en az 3 karakter
    "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
    "start": 0,                 # sayfalama başlangıcı
    "limit": 20,                # maksimum 50
    #"birthYear": "1980",
    "minMatchRate": 95,
    "isDeepSearch": True
}

response = requests.get(
    "https://api.sanctionscanner.com/api/Search/SearchByIdentity",
    params=params,
    auth=HTTPBasicAuth(USERNAME, PASSWORD)
).json()

for item in response["Result"]["Result"]:
    print(f"FullName: {item["FullName"]} |MatchRate: {item["MatchRate"]} | Type: {item["Type"]} | ")


print(f"Temiz mi?: {"Temiz" if len(response["Result"]["Result"]) == 0 else "Sorunlu"} | Pep mi?: ")