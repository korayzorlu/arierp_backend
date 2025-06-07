from django.urls import path, include

from .views import *

app_name = "notifications"

urlpatterns = [
    path('read_notification/', ReadNotificationView.as_view(), name="read_notification"),

    path('api/', include("notifications.api.urls")),
]