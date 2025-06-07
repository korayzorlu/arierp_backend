from django.urls import path, include

from .views import *

app_name = "data"

urlpatterns = [
    
    path('api/', include("data.api.urls")),
]