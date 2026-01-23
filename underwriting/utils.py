import ast
import json
from django.conf import settings

import requests
from requests.auth import HTTPBasicAuth
import re

from common.utils.common_utils import catch_name_from_description

def check_third_person_status(self):
    if self.name is not None and self.name != "" and self.name != "None":
            name = self.name
    else:
        name = catch_name_from_description(self)

    if name and name != "":
        # Aranacak isim ve isteğe bağlı parametreler
        params = {
            "name": str(name),     # en az 3 karakter
            "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
            "start": 0,                 # sayfalama başlangıcı
            "limit": 20,                # maksimum 50
            #"birthYear": "1980",
            "minMatchRate": 100,
            "isDeepSearch": True
        }

        response = requests.get(
            f"{settings.SANCTION_SCANNER_URL}/api/Search/SearchByName",
            params=params,
            auth=HTTPBasicAuth(settings.SANCTION_SCANNER_USERNAME, settings.SANCTION_SCANNER_PASSWORD)
        ).json()

        #print(response["Result"])
    
        if len(response["Result"]["Result"]) == 0:
           return {"status": "cleared", "details": None}
        else:
            return {"status": "matched", "details": ast.literal_eval(str(response["Result"]["Result"]).replace("'", "\x00").replace('"', "'").replace("\x00", '"'))}
    else:
        return {"status": "matched", "details": None}
    
def check_third_person_status_vpos(name):
    if name and name != "":
        # Aranacak isim ve isteğe bağlı parametreler
        params = {
            "name": str(name),     # en az 3 karakter
            "searchType": 1,            # 0: Any, 1: Individual (varsayılan)
            "start": 0,                 # sayfalama başlangıcı
            "limit": 20,                # maksimum 50
            #"birthYear": "1980",
            "minMatchRate": 100,
            "isDeepSearch": True
        }

        response = requests.get(
            f"{settings.SANCTION_SCANNER_URL}/api/Search/SearchByName",
            params=params,
            auth=HTTPBasicAuth(settings.SANCTION_SCANNER_USERNAME, settings.SANCTION_SCANNER_PASSWORD)
        ).json()

        #print(response["Result"])
    
        if len(response["Result"]["Result"]) == 0:
           return {"status": "cleared", "details": None}
        else:
            return {"status": "matched", "details": ast.literal_eval(str(response["Result"]["Result"]).replace("'", "\x00").replace('"', "'").replace("\x00", '"'))}
    else:
        return {"status": "matched", "details": None}