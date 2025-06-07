from django.urls import path, include

from .views import *

app_name = "common"

urlpatterns = [
    
    path('api/', include("common.api.urls")),
]