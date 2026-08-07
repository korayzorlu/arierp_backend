from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'real_estate_agents',RealEstateAgentList, "real_estate_agents_api")
router.register(r'whatsapp_messages',WhatsappMessageList, "whatsapp_messages_api")


urlpatterns = [
    path('',include(router.urls)),
]
