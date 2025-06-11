from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'banka_hareketleri', BankaHareketiList, "banka_hareketleri_api")
router.register(r'banka_tahsilatlari', BankaTahsilatiList, "banka_tahsilatlari_api")
router.register(r'banka_tahsilatlari_odoo', BankaTahsilatiOdooList, "banka_tahsilatlari_odoo_api")


urlpatterns = [
    path('',include(router.urls)),
]
