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

        with open(os.path.join(settings.BASE_DIR, "static/json/city-all.json"), "r") as f:
            countries = sorted(json.load(f)["data"], key=lambda x: x["country"])
        
        new_cities = []

        index = 0
        for country in countries:
            print(country["country"])

            if not country["cities"]:
                continue
                
            if Country.objects.filter(iso2 = country["iso2"]).exists():
                for city in country["cities"]:
                    country_data = Country.objects.filter(iso2 = country["iso2"]).first()
                    new_cities.append({
                        "model" : "common.city",
                        "pk" : index + 1,
                        "fields" : {
                            "country" : country_data.id,
                            "name" : city,
                        }
                    })
                    index += 1

        with open(os.path.join(settings.BASE_DIR, "common/fixtures/city-all-model.json"), "w") as f:
            json.dump(new_cities, f)
        
        print("done!")