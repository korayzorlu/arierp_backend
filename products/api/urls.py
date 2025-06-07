from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'categories', CategoryList, "categories_api")
router.register(r'products', ProductList, "products_api")

urlpatterns = [
    path('',include(router.urls)),
]