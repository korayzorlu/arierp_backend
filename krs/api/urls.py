from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'kapama_detaylari',KapamaDetayList, "kapama_detaylari_api")
router.register(r'kapama_hareketleri',KapamaHareketiList, "kapama_hareketleri_api")

urlpatterns = [
    path('',include(router.urls)),
]
