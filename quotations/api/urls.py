from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'quick_quotations',QuickQuotationList, "quick_quotations_api")
router.register(r'quotations',QuotationList, "quotations_api")

urlpatterns = [
    path('',include(router.urls)),
]
