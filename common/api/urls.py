from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'countries', CountryList, "countries_api")
router.register(r'cities', CityList, "cities_api")
router.register(r'currencies', CurrencyList, "currencies_api")
router.register(r'import_processes', ImportProcessList, "import_processes_api")

urlpatterns = [
    path('',include(router.urls)),
]
