from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'users', UserList, "users_api")
router.register(r'user_profiles', UserProfileList, "user_profiles_api")

urlpatterns = [
    path('',include(router.urls)),
]
