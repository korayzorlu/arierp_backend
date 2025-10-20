from django.urls import path, include

from .views.sms_views import *

app_name = "communication"

urlpatterns = [
    path('send_sms/', SendSMSView.as_view(), name="send_sms"),

    path('', include("communication.api.urls")),
]