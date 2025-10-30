from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'projects',ProjectList, "projects_api")
router.register(r'parcels',ParcelList, "parcels_api")
router.register(r'real_estates',RealEstateList, "real_estates_api")

urlpatterns = [
    path('',include(router.urls)),
]
