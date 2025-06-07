from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'cari_hesap_hareketleri', CariHesapHareketleriList, "cari_hesap_hareketleri_api")
router.register(r'personeller', PersonellerList, "personeller_api")
router.register(r'personel_tahakkuklari', PersonelTahakkuklariList, "personel_tahakkuklari_api")

urlpatterns = [
    path('',include(router.urls)),
]
