from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'notifications', NotificationList, "notifications_api")

urlpatterns = [
    path('',include(router.urls)),
]
