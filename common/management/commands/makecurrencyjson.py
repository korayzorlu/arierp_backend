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

        with open(os.path.join(settings.BASE_DIR, "static/json/curr.json"), "r") as f:
            currs = json.load(f)
            currs = list(currs["conversion_rates"].keys())
            currs.sort()

        currency_list = []

        for country in countries:
            try:
                currency_codes = list(country["currencies"].keys())
                for currency_code in currency_codes:
                    currency_list.append({
                        "code" : currency_code,
                        "name" : country["currencies"][currency_code]["name"],
                        "symbol" : country["currencies"][currency_code]["symbol"]
                    })
            except Exception as e:
                continue

        currency_list_unique = []
        currency_code_list_seen = []
        for currency in currency_list:
            if currency["code"] not in currency_code_list_seen:
                if currency["code"] in currs:
                    currency_list_unique.append(currency)
                    currency_code_list_seen.append(currency["code"])

        currency_list = currency_list_unique
        currency_list.sort(key=lambda x: x["code"])
        
        new_currencies = []
        for index,currency in enumerate(currency_list):
            currency["countries"] = []
            for country in countries:
                if currency["code"] in country.get("currencies",{}):
                    currency["countries"].append(country["cca2"])
            print(currency)
            new_currencies.append({
                "model" : "common.currency",
                "pk" : index + 1,
                "fields" : {
                    "countries" : [c.pk for c in Country.objects.filter(iso2__in=currency["countries"])],
                    "code" : currency["code"],
                    "name" : currency["name"],
                    "symbol" : currency["symbol"],
                    "exchange_rate" : 0
                }
            })
        
        with open(os.path.join(settings.BASE_DIR, "common/fixtures/currency-model.json"), "w") as f:
            json.dump(new_currencies, f)

        print("done!")
        