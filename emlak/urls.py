from django.urls import path, include

from .tests import *

app_name = "emlak"

urlpatterns = [

    path('', include("emlak.api.urls")),
]