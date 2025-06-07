from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from common.models import *

import pandas as pd
import json
import os

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None


    def handle(self, *args, **options):
        print("processing...")

        with open(os.path.join(settings.BASE_DIR, "static/json/country-all.json"), "r") as f:
            countries = sorted(json.load(f), key=lambda x: x["name"]["common"])
            countries = list(filter(lambda x: "root" in x["idd"], countries))
        
        new_countries = []

        for index,country in enumerate(countries):
            print(country["name"]["common"])
            if country["idd"]["root"] == "+1":
                dial_code = f"{country["idd"]["root"]}"
            elif country["cca3"] == "ESH":
                dial_code = "+212"
            elif country["cca3"] == "VAT":
                dial_code = f"{country["idd"]["root"]}{country["idd"]["suffixes"][1]}"
            else:
                dial_code = f"{country["idd"]["root"]}{country["idd"]["suffixes"][0]}"

            if country["cca3"] == "AFG":
                flag = "https://flagcdn.com/af.svg"
            else:
                flag = country["flags"]["svg"]
            
            new_countries.append({
                "model" : "common.country",
                "pk" : index + 1,
                "fields" : {
                    "name" : country["name"]["common"],
                    "formal_name" : country["name"]["official"],
                    "iso2" : country["cca2"],
                    "iso3" : country["cca3"],
                    "dial_code" : dial_code,
                    "emoji" : country["flag"],
                    "flag" : flag
                }
            })

        with open(os.path.join(settings.BASE_DIR, "common/fixtures/country-all-model.json"), "w") as f:
            json.dump(new_countries, f)
        
        print("done!")