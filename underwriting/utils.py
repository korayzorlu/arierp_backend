from django.conf import settings

import requests
from requests.auth import HTTPBasicAuth
import re

def check_third_person_status(self):
    print(settings.SANCTION_SCANNER_PASSWORD)
    if self.name is not None and self.name != "" and self.name != "None":
            name = self.name
    else:
        catched_name = re.search(r"-\s*(.*?)\s*-", self.description)
        if catched_name:
            name = catched_name.group(1)
        else:
            name = ""

    if name and name != "":
        # Aranacak isim ve isteğe bağlı parametreler
        params = {
            "name": str(name),     # en az 3 karakter
            "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
            "start": 0,                 # sayfalama başlangıcı
            "limit": 20,                # maksimum 50
            #"birthYear": "1980",
            "minMatchRate": 95,
            "isDeepSearch": True
        }

        response = requests.get(
            f"{settings.SANCTION_SCANNER_URL}/api/Search/SearchByName",
            params=params,
            auth=HTTPBasicAuth(settings.SANCTION_SCANNER_USERNAME, settings.SANCTION_SCANNER_PASSWORD)
        ).json()

        print(response["Result"])
    
        if len(response["Result"]["Result"]) == 0:
           return 'cleared'
        else:
            return 'matched'
    else:
        return 'matched'