from django.urls import path, include

from .views.sms_views import *
from .views.email_views import *

app_name = "communication"

urlpatterns = [
    path('send_sms/', SendSMSView.as_view(), name="send_sms"),
    path('send_risk_email/', SendRiskEmailView.as_view(), name="send_risk_email"),
    path('check_sms/', CheckSMSView.as_view(), name="check_sms"),

    path('', include("communication.api.urls")),
]