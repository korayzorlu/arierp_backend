from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'black_list_persons', BlackListPersonList, "black_list_persons_api")
router.register(r'scan_partners', ScanPartnerList, "scan_partners_api")
router.register(r'third_persons', ThirdPersonList, "third_persons_api")

urlpatterns = [
    path('',include(router.urls)),
]
