from django.urls import path, include

from .tests import *

app_name = "krs"

urlpatterns = [
    
    path('', include("krs.api.urls")),
]