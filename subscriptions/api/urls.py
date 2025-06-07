from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'menu_items', MenuItemList, "menu_items_api")

urlpatterns = [
    path('',include(router.urls)),
]
