from django.urls import path, include
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)

from .views import *

app_name = "subscriptions"

urlpatterns = [
    
    path('api/', include("subscriptions.api.urls")),
]