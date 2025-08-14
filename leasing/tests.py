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
USERNAME = "api_kullanici_adi"
PASSWORD = "api_sifre"

# Aranacak isim ve isteğe bağlı parametreler
params = {
    "name": "Ahmet Yılmaz",     # en az 3 karakter
    "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
    "start": 0,                 # sayfalama başlangıcı
    "limit": 20,                # maksimum 50
    "birthYear": "1980",
    "minMatchRate": 80,
    "isDeepSearch": True
}

# API çağrısı
response = requests.get(
    "https://api.sanctionscanner.com/api/Search/SearchByName",
    params=params,
    auth=HTTPBasicAuth(USERNAME, PASSWORD)
)

# JSON yanıtı işleme
if response.status_code == 200:
    data = response.json()
    if data.get("IsSuccess"):
        print(f"Toplam bulunan kayıt: {data['TotalRecordCount']}")
        for record in data.get("Result", []):
            print(f"- {record['FullName']} ({record['EntityType']}), Eşleşme oranı: %{record['MatchRate']}")
    else:
        print(f"Hata: {data.get('ErrorMessage')}")
else:
    print(f"HTTP Hatası: {response.status_code} - {response.text}")
