import requests
from requests.auth import HTTPBasicAuth

def check_third_person_status(self):
    USERNAME = "960ed49f-7588-467e-9c3c-58a4f32acc2b"
    PASSWORD = "hZu8zUJfwF"

    self.is_third_person = True

    if self.name:
        # Aranacak isim ve isteğe bağlı parametreler
        params = {
            "name": str(self.name),     # en az 3 karakter
            "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
            "start": 0,                 # sayfalama başlangıcı
            "limit": 20,                # maksimum 50
            #"birthYear": "1980",
            "minMatchRate": 95,
            "isDeepSearch": True
        }

        response = requests.get(
            "https://sandbox-api.sanctionscanner.com/api/Search/SearchByName",
            params=params,
            auth=HTTPBasicAuth(USERNAME, PASSWORD)
        ).json()

        print(response["Result"])
    
        if len(response["Result"]["Result"]) == 0:
            self.is_reliable_person = True
        else:
            self.is_reliable_person = False
    else:
        self.is_reliable_person = False