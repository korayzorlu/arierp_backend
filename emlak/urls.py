from django.urls import path, include

from .tests import *
from .views import *

app_name = "emlak"

urlpatterns = [
    path('make_whatsapp_message/', MakeWhatsappMessageView.as_view(), name="make_whatsapp_message"),
    path('delete_whatsapp_message/', DeleteWhatsappMessageView.as_view(), name="delete_whatsapp_message"),

    path('', include("emlak.api.urls")),
]